"""
FastAPI 后端
提供 REST API 给 Vue 前端调用
"""

import os
import threading
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from src.config import DATA_DIR, CHROMA_DIR, ALLOWED_EXTENSIONS


# ── FastAPI 实例 ──────────────────────────────────────

app = FastAPI(title="biograph API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── 请求模型 ──────────────────────────────────────────

class AskRequest(BaseModel):
    question: str
    top_k: int = 20
    top_n: int = 3


# ── 懒加载单例 ────────────────────────────────────────
# Retriever 和 Generator 都很重（加载 GPU 模型）
# 只在第一次请求时初始化，之后复用

_retriever = None
_generator = None
_indexing = False


def get_retriever():
    global _retriever
    if _retriever is None:
        from src.retriever import Retriever
        _retriever = Retriever()
    return _retriever


def get_generator():
    global _generator
    if _generator is None:
        from src.generator import Generator
        _generator = Generator()
    return _generator


# ── 问答接口 ──────────────────────────────────────────

@app.post("/api/v1/qa/ask")
def ask(req: AskRequest):
    """提问 → 检索 → LLM 生成回答"""
    if not CHROMA_DIR.exists():
        raise HTTPException(400, "索引不存在，请先上传文档并构建索引")

    try:
        retriever = get_retriever()
        generator = get_generator()
    except Exception as e:
        raise HTTPException(500, f"模型初始化失败: {e}")

    try:
        results = retriever.retrieve(req.question, top_k=req.top_k, top_n=req.top_n)
        answer = generator.generate(req.question, results)
    except Exception as e:
        raise HTTPException(500, f"问答失败: {e}")

    return {
        "answer": answer["answer"],
        "sources": answer["sources"],
        "references": results,
    }


# ── 文档管理接口 ──────────────────────────────────────

@app.get("/api/v1/documents")
def list_documents():
    """列出 data/ 目录下的所有文档"""
    docs = []
    for f in sorted(DATA_DIR.iterdir()):
        if f.suffix.lower() in ALLOWED_EXTENSIONS:
            stat = f.stat()
            docs.append({
                "name": f.name,
                "size": stat.st_size,
                "modified": stat.st_mtime,
            })
    return {"documents": docs}


@app.post("/api/v1/documents/upload")
async def upload_document(file: UploadFile = File(...)):
    """上传文档到 data/ 目录"""
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, f"不支持的文件格式: {ext}")

    save_path = DATA_DIR / Path(file.filename).name
    content = await file.read()
    save_path.write_bytes(content)

    return {"message": f"已上传: {file.filename}", "size": len(content)}


@app.delete("/api/v1/documents/{filename}")
def delete_document(filename: str):
    """删除指定文档"""
    target = DATA_DIR / filename
    if not target.exists():
        raise HTTPException(404, f"文件不存在: {filename}")
    target.unlink()
    return {"message": f"已删除: {filename}"}


# ── 索引构建接口 ──────────────────────────────────────

@app.post("/api/v1/documents/index")
def build_index():
    """触发索引构建（后台线程）"""
    global _indexing
    if _indexing:
        raise HTTPException(409, "索引正在构建中，请稍后再试")
    if not DATA_DIR.exists():
        raise HTTPException(400, "data/ 目录不存在")

    _indexing = True

    def _run():
        global _indexing
        try:
            from src.loader import load_documents
            from src.indexer import chunk_text, build_index as _build_index

            docs = load_documents(DATA_DIR)
            all_chunks = []
            for doc in docs:
                chunks = chunk_text(doc["content"], doc["source"])
                all_chunks.extend(chunks)

            if all_chunks:
                _build_index(all_chunks)
        finally:
            _indexing = False

    threading.Thread(target=_run, daemon=True).start()
    return {"message": "索引构建已开始"}


@app.get("/api/v1/documents/index/status")
def index_status():
    """查询索引构建状态"""
    return {"indexing": _indexing, "exists": CHROMA_DIR.exists()}


# ── 统计接口 ──────────────────────────────────────────

@app.get("/api/v1/stats")
def stats():
    """返回基本统计信息"""
    doc_count = len(list(DATA_DIR.glob("*"))) if DATA_DIR.exists() else 0
    chunk_count = 0
    if CHROMA_DIR.exists():
        try:
            import chromadb
            client = chromadb.PersistentClient(path=str(CHROMA_DIR))
            try:
                col = client.get_collection("biograph")
                chunk_count = col.count()
            except Exception:
                pass
        except Exception:
            pass

    return {
        "document_count": doc_count,
        "chunk_count": chunk_count,
        "index_exists": CHROMA_DIR.exists(),
    }


# ── 静态文件服务（Vue 构建产物）──────────────────────

DIST_DIR = Path(__file__).resolve().parent.parent / "frontend" / "dist"

if DIST_DIR.exists():
    app.mount("/assets", StaticFiles(directory=DIST_DIR / "assets"), name="assets")

    @app.get("/{full_path:path}")
    def serve_spa(full_path: str):
        """SPA 路由：所有非 API 请求返回 index.html"""
        file_path = DIST_DIR / full_path
        if file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(DIST_DIR / "index.html")
