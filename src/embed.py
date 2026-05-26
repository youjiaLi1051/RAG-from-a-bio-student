"""
文档切块 + Embedding 脚本
使用 BAAI/bge-m3 模型，生成 dense + sparse 向量，存入 ChromaDB
"""

import os
import re
from pathlib import Path
from FlagEmbedding import BGEM3FlagModel
import chromadb


# ========== 配置 ==========
DATA_DIR = Path(__file__).parent.parent / "data"
DB_DIR = Path(__file__).parent.parent / "chroma_db"
COLLECTION_NAME = "biology_kb"
CHUNK_SIZE = 512       # 每个 chunk 最大字符数
CHUNK_OVERLAP = 64     # chunk 之间重叠字符数


# ========== 1. 加载文档 ==========
def load_documents(data_dir: Path) -> list[dict]:
    """加载 data 目录下所有 .txt 文件"""
    documents = []
    for file_path in sorted(data_dir.glob("*.txt")):
        text = file_path.read_text(encoding="utf-8")
        documents.append({
            "source": file_path.name,
            "content": text,
        })
        print(f"  已加载: {file_path.name} ({len(text)} 字符)")
    return documents


# ========== 2. 文本切块 ==========
def chunk_text(text: str, source: str, chunk_size: int, overlap: int) -> list[dict]:
    """
    按段落优先、字符数兜底的方式切块
    优先在段落边界切分，保持语义完整性
    """
    # 先按段落分割
    paragraphs = re.split(r'\n\s*\n', text)

    chunks = []
    current_chunk = ""

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        # 如果当前 chunk 加上新段落不超限，就合并
        if len(current_chunk) + len(para) + 1 <= chunk_size:
            current_chunk += ("\n" + para if current_chunk else para)
        else:
            # 先把当前 chunk 存起来
            if current_chunk:
                chunks.append(current_chunk)
            # 如果单个段落就超限，按字符数硬切
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

    # 给每个 chunk 加上元数据
    return [
        {
            "content": chunk,
            "source": source,
            "chunk_id": f"{source}::chunk_{i}",
        }
        for i, chunk in enumerate(chunks)
    ]


# ========== 3. Embedding + 存储 ==========
def build_index(chunks: list[dict]):
    """用 bge-m3 生成 embedding 并存入 ChromaDB"""

    print("\n加载 bge-m3 模型...")
    model = BGEM3FlagModel("D:/biograph/.cache/hub/models--BAAI--bge-m3/snapshots/5617a9f61b028005a4858fdac845db406aefb181", use_fp16=True)

    print(f"共 {len(chunks)} 个 chunk，开始编码...")

    texts = [c["content"] for c in chunks]

    # bge-m3 同时输出 dense 和 sparse
    output = model.encode(
        texts,
        batch_size=8,
        max_length=512,      # chunk 已经切好了，不需要太长
        return_dense=True,
        return_sparse=True,
        return_colbert_vecs=False,  # ColBERT 暂不用，省空间
    )

    dense_vecs = output["dense_vecs"]
    sparse_weights = output["lexical_weights"]

    print(f"编码完成，dense 向量维度: {dense_vecs.shape[1]}")

    # 存入 ChromaDB
    print("存入 ChromaDB...")
    client = chromadb.PersistentClient(path=str(DB_DIR))

    # 如果已存在同名集合，先删除重建
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass

    collection = client.create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},  # 用余弦相似度
    )

    # ChromaDB 不直接支持 sparse，先只存 dense
    # sparse 后面可以用 Vespa 或 Milvus 做混合检索
    ids = [c["chunk_id"] for c in chunks]
    documents = texts
    metadatas = [{"source": c["source"]} for c in chunks]

    collection.add(
        ids=ids,
        embeddings=dense_vecs.tolist(),
        documents=documents,
        metadatas=metadatas,
    )

    print(f"已存储 {len(chunks)} 个 chunk 到集合 '{COLLECTION_NAME}'")

    # 保存 sparse 权重备用（ChromaDB 不支持，先存文件）
    import json
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


# ========== 4. 测试检索 ==========
def test_search(collection, query: str):
    """测试检索效果"""
    print(f"\n{'='*50}")
    print(f"查询: {query}")
    print(f"{'='*50}")

    model = BGEM3FlagModel("D:/biograph/.cache/hub/models--BAAI--bge-m3/snapshots/5617a9f61b028005a4858fdac845db406aefb181", use_fp16=True)
    query_vec = model.encode([query], return_dense=True, return_colbert_vecs=False)["dense_vecs"]

    results = collection.query(
        query_embeddings=query_vec.tolist(),
        n_results=3,
    )

    for i, (doc, meta, dist) in enumerate(zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    )):
        print(f"\n--- 结果 {i+1} (相似度: {1 - dist:.4f}) ---")
        print(f"来源: {meta['source']}")
        print(f"内容: {doc[:200]}...")


# ========== 主流程 ==========
if __name__ == "__main__":
    print("=" * 50)
    print("生物知识库构建 - 测试")
    print("=" * 50)

    # 1. 加载文档
    print("\n[1/3] 加载文档...")
    docs = load_documents(DATA_DIR)

    # 2. 切块
    print("\n[2/3] 文本切块...")
    all_chunks = []
    for doc in docs:
        chunks = chunk_text(doc["content"], doc["source"], CHUNK_SIZE, CHUNK_OVERLAP)
        all_chunks.extend(chunks)
        print(f"  {doc['source']} -> {len(chunks)} 个 chunk")
    print(f"  总计: {len(all_chunks)} 个 chunk")

    # 3. 构建索引
    print("\n[3/3] Embedding + 存储...")
    collection = build_index(all_chunks)

    # 4. 测试检索
    test_search(collection, "什么是细胞凋亡？")
    test_search(collection, "DNA复制需要哪些酶？")
    test_search(collection, "PCR的原理是什么？")

    print("\n完成！")
