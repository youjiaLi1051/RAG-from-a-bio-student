"""
索引构建模块
文档加载 → 切块 → bge-m3 编码 → 存入 ChromaDB
"""

import json
import re
from pathlib import Path

import chromadb
from FlagEmbedding import BGEM3FlagModel

from src.loader import load_documents


PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DB_DIR = PROJECT_ROOT / "chroma_db"
MODELS_DIR = PROJECT_ROOT / "models"
EMBED_MODEL_PATH = MODELS_DIR / "bge-m3"
COLLECTION_NAME = "biology_kb"
CHUNK_SIZE = 512
CHUNK_OVERLAP = 64


def chunk_text(text: str, source: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[dict]:
    """按段落优先、字符数兜底的方式切块"""
    paragraphs = re.split(r'\n\s*\n', text)

    chunks = []
    current_chunk = ""

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        if len(current_chunk) + len(para) + 1 <= chunk_size:
            current_chunk += ("\n" + para if current_chunk else para)
        else:
            if current_chunk:
                chunks.append(current_chunk)
            if len(para) > chunk_size:
                for i in range(0, len(para), chunk_size - overlap):
                    chunk = para[i:i + chunk_size]
                    if chunk:
                        chunks.append(chunk)
            else:
                current_chunk = para
                continue
            current_chunk = ""

    if current_chunk:
        chunks.append(current_chunk)

    return [
        {
            "content": chunk,
            "source": source,
            "chunk_id": f"{source}::chunk_{i}",
        }
        for i, chunk in enumerate(chunks)
    ]


def build_index(chunks: list[dict]):
    """用 bge-m3 生成 embedding 并存入 ChromaDB"""

    print("\n加载 bge-m3 模型...")
    model = BGEM3FlagModel(str(EMBED_MODEL_PATH), use_fp16=True)

    print(f"共 {len(chunks)} 个 chunk，开始编码...")

    texts = [c["content"] for c in chunks]

    output = model.encode(
        texts,
        batch_size=8,
        max_length=512,
        return_dense=True,
        return_sparse=True,
        return_colbert_vecs=False,
    )

    dense_vecs = output["dense_vecs"]
    sparse_weights = output["lexical_weights"]

    print(f"编码完成，dense 向量维度: {dense_vecs.shape[1]}")

    print("存入 ChromaDB...")
    client = chromadb.PersistentClient(path=str(DB_DIR))

    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass

    collection = client.create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )

    ids = [c["chunk_id"] for c in chunks]
    metadatas = [{"source": c["source"]} for c in chunks]

    collection.add(
        ids=ids,
        embeddings=dense_vecs.tolist(),
        documents=texts,
        metadatas=metadatas,
    )

    print(f"已存储 {len(chunks)} 个 chunk 到集合 '{COLLECTION_NAME}'")

    sparse_path = DB_DIR / "sparse_weights.json"
    sparse_data = {}
    for i, chunk in enumerate(chunks):
        sparse_data[chunk["chunk_id"]] = {
            "weights": {str(k): float(v) for k, v in sparse_weights[i].items()},
            "source": chunk["source"],
        }
    sparse_path.write_text(json.dumps(sparse_data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"sparse 权重已保存到 {sparse_path}")

    return collection


if __name__ == "__main__":
    print("=" * 50)
    print("知识库索引构建")
    print("=" * 50)

    print("\n[1/3] 加载文档...")
    docs = load_documents(DATA_DIR)

    print("\n[2/3] 文本切块...")
    all_chunks = []
    for doc in docs:
        chunks = chunk_text(doc["content"], doc["source"])
        all_chunks.extend(chunks)
        print(f"  {doc['source']} -> {len(chunks)} 个 chunk")
    print(f"  总计: {len(all_chunks)} 个 chunk")

    print("\n[3/3] Embedding + 存储...")
    build_index(all_chunks)

    print("\n索引构建完成！")
