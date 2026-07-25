from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import CORS_ORIGINS
from app.database import init_db
from app.api import api_router

ADMIN_BUILD = Path(__file__).resolve().parent.parent / "admin" / "build"


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Ynchen. ~ Backend", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 一行挂载所有 API 路由
app.include_router(api_router)

# 挂载上传文件目录
uploads_dir = Path(__file__).resolve().parent.parent / "uploads"
uploads_dir.mkdir(exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(uploads_dir)), name="uploads")

# 挂载 Vue 管理后台（SPA fallback：静态文件优先，子路由回退到 index.html）
if ADMIN_BUILD.exists():

    @app.get("/admin")
    async def admin_index():
        return FileResponse(ADMIN_BUILD / "index.html")

    @app.get("/admin/{full_path:path}")
    async def admin_spa(full_path: str):
        file_path = ADMIN_BUILD / full_path
        if file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(ADMIN_BUILD / "index.html")


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/routes")
def get_routes():
    return {"code": 0, "message": "success", "data": []}
