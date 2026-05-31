# Biograph - 个人知识库问答系统

基于 RAG（检索增强生成）的本地知识库问答系统。上传文档，构建索引，即可通过自然语言提问获取精准回答。

## 功能特性

- **多格式文档支持**：Markdown、TXT、Word (.docx)、PDF，自动解析为纯文本
- **智能检索**：两阶段检索 —— 向量粗筛 + 重排序精排，提升准确率
- **LLM 问答**：支持任意 OpenAI 兼容 API（MiMo、OpenAI、DeepSeek 等）
- **Web 界面**：Vue 3 + Tailwind 构建的现代化前端
- **聊天记录**：自动保存问答历史
- **安全设计**：API Key 存储在服务端，不暴露给前端

## 技术栈

| 模块 | 技术 |
|------|------|
| Embedding | BAAI/bge-m3 |
| 重排序 | BAAI/bge-reranker-v2-m3 |
| 向量数据库 | ChromaDB |
| LLM 接口 | OpenAI 兼容协议 |
| 后端 | FastAPI |
| 前端 | Vue 3 + Tailwind CSS |

## 快速开始

### 环境要求

- Python 3.12+
- Node.js 18+（仅构建前端时需要）
- 显卡推荐 RTX 3060 或更高（CPU 也可运行）

### 安装

```bash
# 克隆项目
git clone https://github.com/your-username/biograph.git
cd biograph

# 创建虚拟环境并安装依赖
uv venv
uv pip install -r pyproject.toml

# 安装前端依赖并构建
cd frontend
npm install
npm run build
cd ..
```

### 启动

```bash
python run_server.py
```

打开浏览器访问 `http://localhost:8000`

### 使用流程

1. 在「设置」页面配置 LLM（API URL、API Key、模型名称）
2. 在「文件」页面上传文档到 `data/` 目录
3. 点击「构建索引」
4. 在「聊天」页面开始问答

## 项目结构

```
biograph/
├── src/
│   ├── api.py          # FastAPI 后端
│   ├── config.py       # 共享配置
│   ├── generator.py    # LLM 生成
│   ├── indexer.py      # 索引构建
│   ├── loader.py       # 文档加载
│   ├── retriever.py    # 检索管线
│   └── reranker.py     # 重排序模型
├── frontend/
│   ├── src/views/      # Vue 页面
│   └── src/api.js      # 前端 API 客户端
├── data/               # 用户文档目录
├── models/             # 模型文件（不提交）
├── chroma_db/          # 向量数据库（不提交）
└── run_server.py       # 启动入口
```

## 检索架构

```
用户问题
  ↓
bge-m3 编码 → ChromaDB 向量检索 (top-20)
  ↓
bge-reranker-v2-m3 精排 → 返回 top-3
  ↓
LLM 基于检索结果生成回答
```

## 配置说明

LLM 配置保存在 `data/llm_config.json`（已在 .gitignore 中，不会提交到仓库）。

支持任何 OpenAI 兼容 API，例如：
- 小米 MiMo：`https://token-plan-cn.xiaomimimo.com/v1`
- OpenAI：`https://api.openai.com/v1`
- DeepSeek：`https://api.deepseek.com`

## License

MIT
