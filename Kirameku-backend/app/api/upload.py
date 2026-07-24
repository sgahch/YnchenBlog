import uuid
from io import BytesIO

from minio import Minio
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from PIL import Image

from app.deps import get_current_user
from app.config import (
    MINIO_ENDPOINT,
    MINIO_ACCESS_KEY,
    MINIO_SECRET_KEY,
    MINIO_BUCKET,
    MINIO_SECURE,
    MINIO_PUBLIC_URL,
)

router = APIRouter(prefix="/api/upload", tags=["上传"])

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif", "image/svg+xml"}
MAX_SIZE = 10 * 1024 * 1024  # 10MB


def _get_client() -> Minio:
    return Minio(
        endpoint=MINIO_ENDPOINT,
        access_key=MINIO_ACCESS_KEY,
        secret_key=MINIO_SECRET_KEY,
        secure=MINIO_SECURE,
    )


def _ensure_bucket(client: Minio):
    """确保 bucket 存在且为公开可读。"""
    if not client.bucket_exists(MINIO_BUCKET):
        client.make_bucket(MINIO_BUCKET)
        # 设置 bucket 为公开读
        policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"AWS": ["*"]},
                    "Action": ["s3:GetObject"],
                    "Resource": [f"arn:aws:s3:::{MINIO_BUCKET}/*"],
                }
            ],
        }
        client.set_bucket_policy(MINIO_BUCKET, policy)


@router.post("/image")
async def upload_image(
    file: UploadFile = File(...),
    _: dict = Depends(get_current_user),
):
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(400, f"不支持的文件类型: {file.content_type}")

    content = await file.read()
    if len(content) > MAX_SIZE:
        raise HTTPException(400, "文件大小不能超过 10MB")

    # 检测方向
    orientation = "landscape"
    try:
        img = Image.open(BytesIO(content))
        w, h = img.size
        orientation = "landscape" if w >= h else "portrait"
    except Exception:
        pass

    # 生成文件名
    ext = file.filename.split(".")[-1] if file.filename and "." in file.filename else "webp"
    filename = f"{uuid.uuid4().hex}.{ext}"

    # 上传到 MinIO
    client = _get_client()
    _ensure_bucket(client)
    client.put_object(
        bucket_name=MINIO_BUCKET,
        object_name=filename,
        data=BytesIO(content),
        length=len(content),
        content_type=file.content_type,
    )

    url = f"{MINIO_PUBLIC_URL.rstrip('/')}/{filename}"
    return {"url": url, "orientation": orientation}
