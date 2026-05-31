"""
FastAPI 后端
提供 REST API 给 Vue 前端调用
"""

import json
import threading
import uuid
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from src.config import DATA_DIR, CHROMA_DIR, PROJECT_ROOT, ALLOWED_EXTENSIONS, LLM_CONFIG_FILE


# ── FastAPI 实例 ──────────────────────────────────────

app = FastAPI(title="biograph API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── 请求模型 ──────────────────────────────────────────

class LLMConfig(BaseModel):
    api_url: str | None = None
    api_key: str | None = None
    model: str | None = None


class AskRequest(BaseModel):
    question: str
    top_k: int = 20
    top_n: int = 3


# ── 全局状态 ──────────────────────────────────────────

_retriever = None
_generator = None
_indexing = False
_models_ready = False


# ── 模型预加载（服务器启动时执行）────────────────────

@app.on_event("startup")
def load_models():
    """服务器启动时预加载模型，避免首次请求等待"""
    global _retriever, _generator, _models_ready

    print("\n" + "=" * 50)
    print("Pre-loading models...")
    print("=" * 50)

    try:
        from src.retriever import Retriever
        _retriever = Retriever()
        # 预加载 reranker（否则首次查询才加载，很慢）
        _retriever._reranker._ensure_loaded()
        print("[OK] Retriever + Reranker loaded")
    except Exception as e:
        print(f"[WARN] Retriever failed: {e}")

    try:
        from src.generator import Generator
        _generator = Generator()
        print("[OK] Generator loaded")
    except Exception as e:
        print(f"[WARN] Generator failed: {e}")

    _models_ready = True
    print("=" * 50 + "\n")


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


# ── 聊天记录存储 ──────────────────────────────────────

HISTORY_FILE = PROJECT_ROOT / "data" / "chat_history.json"


def _load_history() -> list[dict]:
    if HISTORY_FILE.exists():
        return json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
    return []


def _save_history(history: list[dict]):
    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    HISTORY_FILE.write_text(
        json.dumps(history, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


# ── 问答接口 ──────────────────────────────────────────

@app.post("/api/v1/qa/ask")
def ask(req: AskRequest):
    """提问 → 检索 → LLM 生成回答 → 保存记录"""
    import time
    t0 = time.time()

    if not CHROMA_DIR.exists():
        raise HTTPException(400, "索引不存在，请先上传文档并构建索引")

    try:
        retriever = get_retriever()
    except Exception as e:
        raise HTTPException(500, f"检索模型未就绪: {e}")

    # 使用服务端存储的配置
    try:
        generator = get_generator()
    except Exception as e:
        raise HTTPException(500, f"模型未就绪: {e}")

    t1 = time.time()

    try:
        results = retriever.retrieve(req.question, top_k=req.top_k, top_n=req.top_n)
        t2 = time.time()
        answer = generator.generate(req.question, results)
        t3 = time.time()
        print(f"[Timing] retrieve: {t2-t1:.1f}s | generate: {t3-t2:.1f}s | total: {t3-t0:.1f}s")
    except Exception as e:
        raise HTTPException(500, f"问答失败: {e}")

    # 保存聊天记录
    record = {
        "id": str(uuid.uuid4()),
        "question": req.question,
        "answer": answer["answer"],
        "sources": answer["sources"],
        "timestamp": datetime.now().isoformat(),
    }
    history = _load_history()
    history.append(record)
    _save_history(history)

    return {
        "id": record["id"],
        "answer": answer["answer"],
        "sources": answer["sources"],
        "references": results,
    }


@app.get("/api/v1/qa/history")
def get_history(limit: int = 50):
    """获取聊天记录"""
    history = _load_history()
    return {"history": history[-limit:][::-1]}  # 最新的在前


@app.delete("/api/v1/qa/history")
def clear_history():
    """清空聊天记录"""
    _save_history([])
    return {"message": "聊天记录已清空"}


# ── LLM 配置管理 ──────────────────────────────────────

def _load_llm_config() -> dict:
    """从文件读取 LLM 配置"""
    if LLM_CONFIG_FILE.exists():
        import json
        return json.loads(LLM_CONFIG_FILE.read_text(encoding="utf-8"))
    return {}


def _save_llm_config(config: dict):
    """保存 LLM 配置到文件"""
    import json
    LLM_CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    LLM_CONFIG_FILE.write_text(
        json.dumps(config, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


@app.get("/api/v1/settings/llm")
def get_llm_settings():
    """获取 LLM 配置（不返回 api_key）"""
    config = _load_llm_config()
    return {
        "api_url": config.get("api_url", ""),
        "model": config.get("model", ""),
        "configured": bool(config.get("api_key")),
    }


@app.post("/api/v1/settings/llm")
def save_llm_settings(req: LLMConfig):
    """保存 LLM 配置"""
    config = _load_llm_config()
    if req.api_url is not None:
        config["api_url"] = req.api_url
    if req.api_key is not None:
        config["api_key"] = req.api_key
    if req.model is not None:
        config["model"] = req.model
    _save_llm_config(config)

    # 重置 generator 使其使用新配置
    global _generator
    _generator = None

    return {"message": "设置已保存", "configured": bool(config.get("api_key"))}


# ── 文档管理接口 ──────────────────────────────────────

@app.get("/api/v1/documents")
def list_documents():
    """列出 data/ 目录下的所有文档"""
    docs = []
    if DATA_DIR.exists():
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
    """删除文档并重建索引"""
    target = DATA_DIR / filename
    if not target.exists():
        raise HTTPException(404, f"文件不存在: {filename}")
    target.unlink()

    # 自动重建索引（后台线程）
    _trigger_rebuild()

    return {"message": f"已删除: {filename}，索引正在重建"}


def _trigger_rebuild():
    """后台重建索引"""
    global _indexing, _retriever
    if _indexing:
        return

    _indexing = True

    def _run():
        global _indexing, _retriever
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

            # 索引重建后，重置 Retriever 以使用新集合
            _retriever = None
            print("Retriever reset, will reload on next query")
        except Exception as e:
            print(f"Index rebuild failed: {e}")
        finally:
            _indexing = False

    threading.Thread(target=_run, daemon=True).start()


# ── 索引构建接口 ──────────────────────────────────────

@app.post("/api/v1/documents/index")
def build_index():
    """手动触发索引构建"""
    global _indexing
    if _indexing:
        raise HTTPException(409, "索引正在构建中，请稍后再试")
    if not DATA_DIR.exists():
        raise HTTPException(400, "data/ 目录不存在")

    _trigger_rebuild()
    return {"message": "索引构建已开始"}


@app.get("/api/v1/documents/index/status")
def index_status():
    """查询索引构建状态"""
    return {"indexing": _indexing, "exists": CHROMA_DIR.exists()}


# ── 统计接口 ──────────────────────────────────────────

@app.get("/api/v1/stats")
def stats():
    """返回基本统计信息"""
    doc_count = 0
    if DATA_DIR.exists():
        doc_count = len([f for f in DATA_DIR.iterdir() if f.suffix.lower() in ALLOWED_EXTENSIONS])

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
        "models_ready": _models_ready,
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
