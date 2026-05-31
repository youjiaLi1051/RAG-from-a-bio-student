"""
LLM 生成模块
接收检索结果 + 用户问题，调用 MiMo API 生成回答
"""

import os

from dotenv import load_dotenv
from openai import OpenAI

from src.config import MIMO_API_BASE, MIMO_MODEL

load_dotenv()

SYSTEM_PROMPT = """你是一个专业的生物学考研辅导助手。请根据提供的参考资料回答学生的问题。

## 回答要求

1. **准确优先**：只基于参考资料回答，不要编造信息。如果资料不足，坦诚说明。
2. **结构清晰**：使用 markdown 格式，合理使用标题、列表、加粗等。
3. **重点突出**：关键概念用**加粗**标注，重要数值用具体数字说明。
4. **适度扩展**：在资料基础上可以补充必要的背景知识，但要标注"补充说明"。
5. **语言风格**：像一个耐心的学长/学姐在讲解，不要太学术化，也不要太口语化。

## 输出格式

- 先给出**直接回答**（1-2句话概括核心答案）
- 再展开**详细解释**（分点或分段）
- 最后可以加**补充说明**或**易错点提醒**（如果有的话）
- 末尾标注**参考来源**（文件名）

## 示例格式

**直接回答：**
RD细胞是该实验使用的主要细胞系。

**详细说明：**
1. **细胞类型**：RD细胞是一种横纹肌肉瘤细胞系...
2. **选择原因**：由于RD细胞具有...特性
3. **培养条件**：...

**参考来源：** 开题报告.md
"""


class Generator:
    def __init__(self, model: str = MIMO_MODEL):
        api_key = os.environ.get("MIMO_API_KEY")
        if not api_key:
            raise ValueError("请设置环境变量 MIMO_API_KEY")

        # miniconda 设置的 SSL_CERT_FILE 指向不存在的文件，会导致 httpx 报错
        if "SSL_CERT_FILE" in os.environ:
            import pathlib
            if not pathlib.Path(os.environ["SSL_CERT_FILE"]).exists():
                del os.environ["SSL_CERT_FILE"]

        self._client = OpenAI(
            api_key="not-used",
            base_url=MIMO_API_BASE,
            default_headers={"api-key": api_key},
        )
        self._model = model

    def generate(self, query: str, contexts: list[dict]) -> dict:
        """
        根据检索到的 context 生成回答
        contexts: [{"content": str, "source": str, ...}, ...]
        返回: {"answer": str, "sources": list[str]}
        """
        context_text = "\n\n".join(
            f"[来源: {c['source']}]\n{c['content']}" for c in contexts
        )

        response = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"参考资料：\n{context_text}\n\n问题：{query}"},
            ],
            temperature=0.3,
        )

        return {
            "answer": response.choices[0].message.content,
            "sources": list({c["source"] for c in contexts}),
        }
