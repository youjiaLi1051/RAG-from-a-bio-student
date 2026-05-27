"""
Reranker 模块
用 bge-reranker-v2-m3 对候选文档重新打分，提升检索精度
"""

from pathlib import Path

from FlagEmbedding import FlagReranker


PROJECT_ROOT = Path(__file__).parent.parent
RERANK_MODEL_PATH = PROJECT_ROOT / "models" / "bge-reranker-v2-m3"


class Reranker:
    def __init__(self, model_path: str = str(RERANK_MODEL_PATH), use_fp16: bool = True):
        self._model_path = model_path
        self._use_fp16 = use_fp16
        self._model = None

    def _ensure_loaded(self):
        if self._model is None:
            print("加载 reranker 模型...")
            self._model = FlagReranker(self._model_path, use_fp16=self._use_fp16)

    def unload(self):
        if self._model is not None:
            import torch
            self._model.model.to("cpu")
            torch.cuda.empty_cache()
            self._model = None
            print("reranker 已卸载")

    def rerank(self, query: str, passages: list[str], top_n: int = 3) -> list[tuple[int, float]]:
        """
        对 passages 重新打分，返回 top_n 个结果
        返回: [(原始索引, 分数), ...] 按分数降序
        """
        self._ensure_loaded()
        pairs = [[query, p] for p in passages]
        scores = self._model.compute_score(pairs, normalize=True)
        ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)
        return ranked[:top_n]