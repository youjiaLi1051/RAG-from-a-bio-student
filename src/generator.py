"""
LLM 生成模块
接收检索结果 + 用户问题，调用 LLM API 生成回答
配置从 data/llm_config.json 读取
"""

import os
import json

from openai import OpenAI

from src.config import LLM_CONFIG_FILE

SYSTEM_PROMPT = """你是一个智能知识库问答助手，擅长基于用户上传的文档回答问题。

## 核心原则
- **忠实原文**：优先基于提供的参考资料回答，不要编造信息
- **坦诚不足**：如果资料不足，明确说明"这部分资料未覆盖"，再给出你的理解（标注"补充说明"）
- **准确引用**：关键信息标注来源文件

## 输出格式

**🎯 直接回答**
（1-2句话概括核心答案）

**📖 详细说明**
（分点展开，关键词用加粗标注）

**💡 补充说明**
（资料未覆盖但相关的内容，如有）

**📎 参考来源**
（标注来自哪些文件）

## 语言风格
- 专业清晰，像一个靠谱的助手在帮你查资料
- 不要太口语化，也不要太学术化
- 适度使用 markdown 格式提升可读性
"""


def _load_llm_config() -> dict:
    """从文件读取 LLM 配置"""
    if LLM_CONFIG_FILE.exists():
        return json.loads(LLM_CONFIG_FILE.read_text(encoding="utf-8"))
    return {}


class Generator:
    def __init__(self, api_url: str | None = None, api_key: str | None = None, model: str | None = None):
        # 优先使用参数，其次读配置文件
        config = _load_llm_config()

        api_url = api_url or config.get("api_url")
        api_key = api_key or config.get("api_key")
        model = model or config.get("model")

        if not api_key:
            raise ValueError("未配置 LLM，请先在设置页面配置 API Key")
        if not api_url:
            raise ValueError("未配置 LLM，请先在设置页面配置 API URL")
        if not model:
            raise ValueError("未配置 LLM，请先在设置页面配置模型名称")

        # miniconda 设置的 SSL_CERT_FILE 指向不存在的文件，会导致 httpx 报错
        if "SSL_CERT_FILE" in os.environ:
            import pathlib
            if not pathlib.Path(os.environ["SSL_CERT_FILE"]).exists():
                del os.environ["SSL_CERT_FILE"]

        self._client = OpenAI(
            api_key="not-used",
            base_url=api_url,
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
