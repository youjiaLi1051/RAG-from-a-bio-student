"""
启动 FastAPI 服务器
端口 8000，同时 serve API 和前端静态文件
"""

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "src.api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
