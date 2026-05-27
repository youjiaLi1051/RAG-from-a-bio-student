"""
LLM 生成模块
接收检索结果 + 用户问题，调用 MiMo API 生成回答
"""

import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


MIMO_BASE_URL = "https://token-plan-cn.xiaomimimo.com/v1"
DEFAULT_MODEL = "mimo-v2.5"

SYSTEM_PROMPT = (
    "你是一个生物学考研助手。根据提供的参考资料回答问题。\n"
    "规则：\n"
    "1. 只基于参考资料回答，不要编造\n"
    "2. 如果参考资料不足以回答，明确说明\n"
    "3. 回答要准确、简洁、有条理\n"
    "4. 适当引用来源"
)


class Generator:
    def __init__(self, model: str = DEFAULT_MODEL):
        api_key = os.environ.get("MIMO_API_KEY")
        if not api_key:
            raise ValueError("请设置环境变量 MIMO_API_KEY")

        self._client = OpenAI(
            api_key="not-used",
            base_url=MIMO_BASE_URL,
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
