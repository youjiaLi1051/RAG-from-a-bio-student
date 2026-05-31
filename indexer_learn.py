"""
索引构建 — 学习版（无 def 封装，一步步看懂）

完整流程：加载文档 → 切块 → bge-m3 编码 → 存入 ChromaDB

运行方式：python indexer_learn.py
"""

import re
import chromadb
from FlagEmbedding import BGEM3FlagModel

from src.config import (
    CHROMA_DIR, COLLECTION_NAME, DATA_DIR, EMBED_MODEL_PATH,
    CHUNK_SIZE, CHUNK_OVERLAP,
)
from src.loader import load_documents


# ============================================================
# 第 1 步：加载文档
# ============================================================
# load_documents() 会扫描 data/ 目录下的 .txt/.md/.docx/.pdf 文件
# 返回格式：[{"source": "文件名", "content": "纯文本内容"}, ...]

print("=" * 50)
print("知识库索引构建（学习版）")
print("=" * 50)

print("\n[1/4] 加载文档...")
docs = load_documents(DATA_DIR)
print(f"  共加载 {len(docs)} 个文档")


# ============================================================
# 第 2 步：文本切块
# ============================================================
# 为什么切块？
#   - embedding 模型有最大输入长度（通常 512 token）
#   - 太长的文本会丢失信息
#   - 切成小块后，检索时能精确定位到具体段落
#
# 切块策略：段落优先
#   1. 按空行（\\n\\n）分割成段落
#   2. 段落短 → 合并到当前块，直到超过 CHUNK_SIZE（512 字符）
#   3. 段落长 → 强制按字符数切割，保留 CHUNK_OVERLAP（64 字符）重叠
#      （重叠是为了避免切断语义）

print("\n[2/4] 文本切块...")

all_chunks = []
for doc in docs:
    source = doc["source"]
    text = doc["content"]

    # 用正则按空行分割成段落
    paragraphs = re.split(r'\n\s*\n', text)

    chunks = []
    current_chunk = ""

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        # 情况 1：当前块 + 新段落 没超过限制 → 合并
        if len(current_chunk) + len(para) + 1 <= CHUNK_SIZE:
            current_chunk += ("\n" + para if current_chunk else para)
        else:
            # 先保存当前已有的块
            if current_chunk:
                chunks.append(current_chunk)

            # 情况 2：单个段落太长 → 强制切割
            if len(para) > CHUNK_SIZE:
                for i in range(0, len(para), CHUNK_SIZE - CHUNK_OVERLAP):
                    chunk = para[i:i + CHUNK_SIZE]
                    if chunk:
                        chunks.append(chunk)
                current_chunk = ""
            else:
                # 情况 3：段落不长，但和当前块一起就超了 → 新块从这个段落开始
                current_chunk = para
                continue

    # 别忘了最后一块
    if current_chunk:
        chunks.append(current_chunk)

    # 给每个 chunk 加上元数据
    for i, chunk in enumerate(chunks):
        all_chunks.append({
            "content": chunk,
            "source": source,
            "chunk_id": f"{source}::chunk_{i}",
        })

    print(f"  {source} -> {len(chunks)} 个 chunk")

print(f"  总计: {len(all_chunks)} 个 chunk")


# ============================================================
# 第 3 步：用 bge-m3 编码成向量
# ============================================================
# bge-m3 是一个 embedding 模型，作用是：
#   输入：一段文字
#   输出：一个高维向量（1024 维的浮点数数组）
#   用途：向量之间的距离 = 语义相似度
#         两个意思相近的句子，向量距离近
#         两个意思无关的句子，向量距离远
#
# use_fp16=True → 用半精度推理，省显存（RTX 3060 6GB 够用）

print("\n[3/4] 加载 bge-m3 模型...")
model = BGEM3FlagModel(str(EMBED_MODEL_PATH), use_fp16=True)

texts = [c["content"] for c in all_chunks]
print(f"  共 {len(texts)} 个 chunk，开始编码...")

output = model.encode(
    texts,
    batch_size=8,       # 每次编码 8 个 chunk
    max_length=512,     # 最大输入长度
    return_dense=True,  # 返回稠密向量（我们只用这个）
    return_colbert_vecs=False,  # 不需要 ColBERT 向量
)

dense_vecs = output["dense_vecs"]
print(f"  编码完成！向量维度: {dense_vecs.shape}")
# dense_vecs.shape = (chunk数量, 1024)
# 例如 (15, 1024) 表示 15 个 chunk，每个是 1024 维向量


# ============================================================
# 第 4 步：存入 ChromaDB
# ============================================================
# ChromaDB 是一个向量数据库，作用是：
#   - 存储向量 + 元数据
#   - 查询时计算向量距离，返回最相似的结果
#   - PersistentClient → 数据持久化到磁盘（关机不丢）

print("\n[4/4] 存入 ChromaDB...")

# 连接（或创建）本地数据库
client = chromadb.PersistentClient(path=str(CHROMA_DIR))

# 如果集合已存在，先删掉（重新构建）
try:
    client.delete_collection(COLLECTION_NAME)
except Exception:
    pass

# 创建集合（类似 SQL 的表）
# hnsw:space = cosine → 用余弦相似度衡量向量距离
collection = client.create_collection(
    name=COLLECTION_NAME,
    metadata={"hnsw:space": "cosine"},
)

# 准备要存的数据
ids = [c["chunk_id"] for c in all_chunks]                    # 每个 chunk 的唯一 ID
metadatas = [{"source": c["source"]} for c in all_chunks]   # 元数据（来源文件名）
embeddings = dense_vecs.tolist()                              # 向量

# 写入 ChromaDB
collection.add(
    ids=ids,
    embeddings=embeddings,
    documents=texts,        # 原始文本（方便检索后直接返回）
    metadatas=metadatas,
)

print(f"  已存储 {len(all_chunks)} 个 chunk 到集合 '{COLLECTION_NAME}'")


# ============================================================
# 完成！
# ============================================================
print("\n" + "=" * 50)
print("索引构建完成！")
print(f"  数据库位置: {CHROMA_DIR}")
print(f"  集合名称:   {COLLECTION_NAME}")
print(f"  chunk 总数: {len(all_chunks)}")
print("=" * 50)
