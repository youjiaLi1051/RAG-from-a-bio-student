"""
检索模块
embedding 粗筛 → reranker 精排 → 返回结果
"""

import chromadb
from FlagEmbedding import BGEM3FlagModel

from src.config import CHROMA_DIR, COLLECTION_NAME, EMBED_MODEL_PATH, RERANKER_MODEL_PATH
from src.reranker import Reranker


class Retriever:
    def __init__(
        self,
        embed_model_path: str = str(EMBED_MODEL_PATH),
        reranker_model_path: str = str(RERANKER_MODEL_PATH),
        db_path: str = str(CHROMA_DIR),
        collection_name: str = COLLECTION_NAME,
    ):
        print("加载 embedding 模型...")
        self._embed_model = BGEM3FlagModel(embed_model_path, use_fp16=True)

        client = chromadb.PersistentClient(path=db_path)
        self._collection = client.get_collection(collection_name)

        self._reranker = Reranker(reranker_model_path)

    def retrieve(self, query: str, top_k: int = 20, top_n: int = 3) -> list[dict]:
        """
        两阶段检索：
        1. embedding 搜索 top_k 候选
        2. reranker 精排返回 top_n
        """
        import time

        # 阶段 1：向量检索
        t0 = time.time()
        query_vec = self._embed_model.encode(
            [query], return_dense=True, return_colbert_vecs=False
        )["dense_vecs"]
        t1 = time.time()
        results = self._collection.query(
            query_embeddings=query_vec.tolist(),
            n_results=top_k,
        )
        t2 = time.time()
        docs = results["documents"][0]
        metas = results["metadatas"][0]
        dists = results["distances"][0]

        # 阶段 2：reranker 精排
        ranked = self._reranker.rerank(query, docs, top_n=top_n)
        t3 = time.time()

        print(f"  [retrieve] encode: {t1-t0:.1f}s | chromadb: {t2-t1:.1f}s | rerank: {t3-t2:.1f}s")

        output = []
        for orig_idx, score in ranked:
            output.append({
                "content": docs[orig_idx],
                "source": metas[orig_idx]["source"],
                "embedding_similarity": 1 - dists[orig_idx],
                "rerank_score": score,
            })
        return output

    def search_only(self, query: str, top_k: int = 3) -> list[dict]:
        """只做 embedding 搜索，不经过 reranker（调试用）"""
        query_vec = self._embed_model.encode(
            [query], return_dense=True, return_colbert_vecs=False
        )["dense_vecs"]
        results = self._collection.query(
            query_embeddings=query_vec.tolist(),
            n_results=top_k,
        )
        output = []
        for doc, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        ):
            output.append({
                "content": doc,
                "source": meta["source"],
                "embedding_similarity": 1 - dist,
            })
        return output

    def unload_reranker(self):
        self._reranker.unload()