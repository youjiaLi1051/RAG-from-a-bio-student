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

| 模块 | 技术 | 说明 |
|------|------|------|
| Embedding | BAAI/bge-m3 | 多语言向量模型，~2.2GB 显存 |
| 重排序 | BAAI/bge-reranker-v2-m3 | 精排模型，~1.2GB 显存 |
| 向量数据库 | ChromaDB | 本地持久化存储 |
| LLM 接口 | OpenAI 兼容协议 | 支持多种 API |
| 后端 | FastAPI | Python 异步框架 |
| 前端 | Vue 3 + Tailwind CSS | 现代化 UI |

## 快速开始

### 环境要求

- **Python**：3.12 或更高
- **Node.js**：18 或更高（仅构建前端时需要）
- **显卡**：推荐 RTX 3060 或更高（CPU 也可运行，速度较慢）
- **内存**：推荐 16GB 以上

### 1. 克隆项目

```bash
git clone https://github.com/youjiaLi1051/RAG-from-a-bio-student.git
cd RAG-from-a-bio-student
```

### 2. 创建虚拟环境并安装依赖

```bash
# 创建虚拟环境
uv venv

# 安装 Python 依赖
uv pip install -r pyproject.toml
```

### 3. 下载模型（重要！）

模型文件不在 Git 仓库中，需要手动下载：

```bash
# 安装 ModelScope（用于下载模型）
uv pip install modelscope

# 下载 bge-m3 embedding 模型（~2.2GB）
python -c "from modelscope import snapshot_download; snapshot_download('BAAI/bge-m3', local_dir='models/bge-m3')"

# 下载 bge-reranker-v2-m3 重排序模型（~1.2GB）
python -c "from modelscope import snapshot_download; snapshot_download('BAAI/bge-reranker-v2-m3', local_dir='models/bge-reranker-v2-m3')"
```

> **注意**：如果使用 HuggingFace，将 `BAAI/bge-m3` 替换为对应的 HF 仓库名。国内推荐使用 ModelScope。

### 4. 构建前端

```bash
cd frontend
npm install
npm run build
cd ..
```

### 5. 启动服务

```bash
python run_server.py
```

打开浏览器访问 `http://localhost:8000`

### 6. 首次配置

1. 打开「设置」页面
2. 填写 LLM 配置：
   - **API URL**：例如 `https://token-plan-cn.xiaomimimo.com/v1`
   - **API Key**：你的 API 密钥
   - **模型名称**：例如 `mimo-v2.5`
3. 点击「保存」

### 7. 上传文档并构建索引

1. 在「文件」页面上传文档（支持 .txt、.md、.docx、.pdf）
2. 点击「构建索引」
3. 等待索引构建完成（取决于文档大小和数量）

### 8. 开始问答

在「聊天」页面输入问题，系统会自动检索相关文档并生成回答。

## 项目结构

```
biograph/
├── src/                    # 后端代码
│   ├── api.py              # FastAPI REST API 端点
│   ├── config.py           # 共享配置（路径常量）
│   ├── generator.py        # LLM 生成模块
│   ├── indexer.py          # 索引构建模块
│   ├── loader.py           # 文档加载模块
│   ├── retriever.py        # 检索管线
│   └── reranker.py         # 重排序模型封装
├── frontend/               # 前端代码
│   ├── src/
│   │   ├── views/          # Vue 页面组件
│   │   ├── api.js          # 前端 API 客户端
│   │   └── App.vue         # 主布局组件
│   └── package.json        # 前端依赖配置
├── data/                   # 用户文档目录
│   └── example.md          # 示例文档
├── models/                 # 模型文件（需要手动下载，不提交到 Git）
│   ├── bge-m3/             # Embedding 模型
│   └── bge-reranker-v2-m3/ # 重排序模型
├── chroma_db/              # 向量数据库（自动生成，不提交到 Git）
├── pyproject.toml          # Python 依赖配置
├── run_server.py           # 启动入口
└── README.md               # 本文件
```

## 检索架构

```
用户问题
  ↓
bge-m3 编码 → 生成 1024 维向量
  ↓
ChromaDB 向量检索 → 返回 top-20 候选文档
  ↓
bge-reranker-v2-m3 精排 → 选出最相关的 top-3
  ↓
LLM 基于检索结果生成回答
```

### 性能指标

- **向量检索**：毫秒级（~10ms）
- **重排序**：几十毫秒（~50ms）
- **LLM 生成**：取决于 API 响应速度
- **总延迟**：通常 1-3 秒

## 配置说明

### LLM 配置

LLM 配置保存在 `data/llm_config.json`（已在 .gitignore 中，不会提交到仓库）。

支持任何 OpenAI 兼容 API：

| 服务商 | API URL | 模型示例 |
|--------|---------|----------|
| 小米 MiMo | `https://token-plan-cn.xiaomimimo.com/v1` | `mimo-v2.5` |
| OpenAI | `https://api.openai.com/v1` | `gpt-4` |
| DeepSeek | `https://api.deepseek.com` | `deepseek-chat` |
| 本地 Ollama | `http://localhost:11434/v1` | `llama3` |

### 文档格式支持

| 格式 | 扩展名 | 说明 |
|------|--------|------|
| 纯文本 | `.txt` | 自动检测编码（UTF-8、GBK 等） |
| Markdown | `.md` | 自动解析为纯文本，去掉标记 |
| Word | `.docx` | 提取段落和表格内容 |
| PDF | `.pdf` | 提取文本和表格 |

## 开发模式

### 前端热重载

```bash
cd frontend
npm run dev
```

前端运行在 `http://localhost:5173`，自动代理 API 请求到 `http://localhost:8000`。

### 重建索引

文档变更后需要重建索引：

```bash
python -m src.indexer
```

或在 Web 界面点击「构建索引」按钮。

## 常见问题

### Q: 模型下载失败怎么办？

A: 国内推荐使用 ModelScope 下载。如果仍然失败，可以：
1. 使用镜像源：`export MODELSCOPE_CACHE=~/.cache/modelscope`
2. 手动下载模型文件放到 `models/` 目录

### Q: 启动时报错 "未配置 LLM"？

A: 需要在设置页面配置 LLM API 信息。配置会保存在 `data/llm_config.json`。

### Q: 索引构建很慢怎么办？

A: 取决于文档大小和数量。首次构建较慢，后续增量更新会快很多。可以考虑：
1. 使用 GPU 加速 embedding 计算
2. 减少文档数量或分批上传

### Q: 如何使用 GPU 加速？

A: 安装 CUDA 版本的 PyTorch：

```bash
uv pip uninstall torch torchvision torchaudio -y
uv pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

> 注意：需要 NVIDIA 显卡和对应的 CUDA 驱动。

### Q: 如何支持更多文档格式？

A: 修改 `src/loader.py`，添加新的解析函数。当前支持：
- `.txt`：直接读取
- `.md`：markdown 解析
- `.docx`：python-docx
- `.pdf`：PyMuPDF

## 依赖说明

主要依赖：

- `FlagEmbedding`：embedding 和 reranker 模型
- `chromadb`：向量数据库
- `transformers`：HuggingFace 模型库
- `fastapi`：Web 框架
- `openai`：LLM API 客户端
- `markdown`：Markdown 解析
- `beautifulsoup4`：HTML 转文本
- `python-docx`：Word 文档解析
- `PyMuPDF`：PDF 解析

完整依赖见 `pyproject.toml`。

## License

MIT

## 致谢

- [BAAI/bge-m3](https://github.com/FlagEmbedding/FlagEmbedding)：Embedding 模型
- [BAAI/bge-reranker-v2-m3](https://github.com/FlagEmbedding/FlagEmbedding)：重排序模型
- [ChromaDB](https://www.trychroma.com/)：向量数据库
- [FastAPI](https://fastapi.tiangolo.com/)：Web 框架
- [Vue.js](https://vuejs.org/)：前端框架
