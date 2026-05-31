# biograph - 个性化知识库

## 项目概述

AI考研训练系统（生物学方向），完整RAG管线：文档加载→索引构建→两阶段检索→LLM生成回答。Vue 3 + Tailwind 前端，FastAPI 后端。

## 项目结构

```
src/
├── config.py        # 共享配置：路径常量、API设置
├── loader.py        # 文档解析：.txt/.md/.docx/.pdf
├── indexer.py        # 建索引：加载文档→切块→bge-m3 embedding→存ChromaDB
├── retriever.py      # 查询管线：embedding搜索→reranker精排→返回结果
├── reranker.py       # reranker模型封装（延迟加载）
├── generator.py      # LLM生成：调用MiMo API基于检索结果生成回答
├── api.py            # FastAPI REST API端点

frontend/
├── src/views/        # Vue页面（ChatView, FilesView, StatsView）
├── src/api.js        # 前端API客户端
├── src/App.vue       # 主布局+导航

models/
├── bge-m3/           # embedding模型（~2.2GB显存）
├── bge-reranker-v2-m3/  # reranker模型（~1.2GB显存）

chroma_db/            # ChromaDB持久化存储（向量数据库）
data/                 # 用户上传的文档
```

## 检索架构

两阶段检索：
1. 用户query → bge-m3编码 → ChromaDB top-20候选（毫秒级）
2. bge-reranker-v2-m3精排 → 返回top-3结果（几十毫秒）

## 关键技术决策

- **建索引和查询严格分离**：indexer.py只管建，retriever.py只管查
- **reranker延迟加载**：首次调用时才加载，用完unload()释放显存
- **embedding模型常驻**：查询时只编码1条query
- **模型下载用ModelScope**：HuggingFace国内下载不稳定，用`from modelscope import snapshot_download`

## 依赖版本约束

- `transformers>=4.45,<5`：FlagEmbedding 1.4.0不兼容transformers 5.x
- 使用uv管理依赖，镜像源：`https://pypi.tuna.tsinghua.edu.cn/simple`

## LLM配置

- API: `https://token-plan-cn.xiaomimimo.com/v1`（小米MiMo，OpenAI兼容协议）
- 模型: `mimo-v2.5h`
- 认证: `api-key` header（非标准 `Authorization: Bearer`），用 `default_headers` 适配
- 环境变量: `MIMO_API_KEY`（必须设置，不写入代码）

## 常用命令

```bash
# 建索引（文档变更后执行）
python -m src.indexer

# 启动Web服务（端口8000，同时serve API和前端）
python run_server.py

# 开发模式（前端热重载）
cd frontend && npm run dev   # 端口5173，自动代理API到8000

# CLI问答（不启动Web服务）
python main.py

# 构建前端（FastAPI serve静态文件）
cd frontend && npm run build
```

## 硬件约束

RTX 3060 Laptop 6GB显存，同时加载embedding(~2.2GB)+reranker(~1.2GB)=~3.4GB，够用。

## Windows注意

输出含Unicode字符时设 `PYTHONIOENCODING=utf-8`，避免GBK编码错误。
