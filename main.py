"""
biograph - RAG 问答入口
用户输入问题 → 检索知识库 → LLM 生成回答
"""

import logging
logging.getLogger("transformers").setLevel(logging.ERROR)

from src.retriever import Retriever
from src.generator import Generator


def main():
    print("=" * 50)
    print("biograph - 生物学考研知识库问答")
    print("=" * 50)

    print("\n初始化检索引擎...")
    retriever = Retriever()

    print("初始化生成模型...")
    generator = Generator()

    print("\n可以开始提问了！输入 q 退出。\n")

    while True:
        query = input("你的问题: ").strip()
        if not query:
            continue
        if query.lower() == "q":
            break

        print("\n检索中...")
        results = retriever.retrieve(query, top_k=20, top_n=3)

        print(f"找到 {len(results)} 条相关内容，生成回答...\n")
        answer = generator.generate(query, results)

        print(f"回答:\n{answer['answer']}")
        print(f"\n参考来源: {', '.join(answer['sources'])}")
        print("-" * 50)

    print("\n再见！")


if __name__ == "__main__":
    main()
