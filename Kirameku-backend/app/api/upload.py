import json
import uuid
import logging
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

logger = logging.getLogger("upload")
logger.setLevel(logging.DEBUG)
if not logger.handlers:
    h = logging.StreamHandler()
    h.setFormatter(logging.Formatter("%(asctime)s [UPLOAD] %(levelname)s %(message)s"))
    logger.addHandler(h)

# 同时开启 MinIO SDK 的底层 HTTP 请求日志（排查连接/认证问题）
logging.getLogger("minio").setLevel(logging.DEBUG)

router = APIRouter(prefix="/api/upload", tags=["上传"])

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif", "image/svg+xml"}
MAX_SIZE = 10 * 1024 * 1024  # 10MB


def _get_client() -> Minio:
    logger.info(f"创建 MinIO 客户端: endpoint={MINIO_ENDPOINT}, secure={MINIO_SECURE}, bucket={MINIO_BUCKET}")
    return Minio(
        endpoint=MINIO_ENDPOINT,
        access_key=MINIO_ACCESS_KEY,
        secret_key=MINIO_SECRET_KEY,
        secure=MINIO_SECURE,
    )


def _ensure_bucket(client: Minio):
    """确保 bucket 存在且为公开可读。"""
    logger.info(f"检查 bucket 是否存在: {MINIO_BUCKET}")
    found = client.bucket_exists(MINIO_BUCKET)
    logger.info(f"bucket_exists({MINIO_BUCKET}) = {found}")

    if not found:
        logger.info(f"创建 bucket: {MINIO_BUCKET}")
        client.make_bucket(MINIO_BUCKET)
        logger.info(f"bucket 创建成功: {MINIO_BUCKET}")

    # 无论 bucket 是否已存在，始终确保公开读策略
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
    logger.info(f"设置 bucket 公开读策略: {MINIO_BUCKET}")
    client.set_bucket_policy(MINIO_BUCKET, json.dumps(policy))
    logger.info(f"bucket 策略设置成功")


@router.post("/image")
async def upload_image(
    file: UploadFile = File(...),
    _: dict = Depends(get_current_user),
):
    logger.info(f"收到上传请求: filename={file.filename}, content_type={file.content_type}")

    # 1. 检查文件类型
    if file.content_type not in ALLOWED_TYPES:
        logger.warning(f"不支持的文件类型: {file.content_type}")
        raise HTTPException(400, f"不支持的文件类型: {file.content_type}")
    logger.info(f"文件类型检查通过: {file.content_type}")

    # 2. 读取文件内容
    content = await file.read()
    logger.info(f"文件读取完成: size={len(content)} bytes")
    if len(content) > MAX_SIZE:
        logger.warning(f"文件过大: {len(content)} > {MAX_SIZE}")
        raise HTTPException(400, "文件大小不能超过 10MB")

    # 3. 检测方向
    orientation = "landscape"
    try:
        img = Image.open(BytesIO(content))
        w, h = img.size
        orientation = "landscape" if w >= h else "portrait"
        logger.info(f"图片尺寸: {w}x{h}, orientation={orientation}")
    except Exception as e:
        logger.warning(f"图片尺寸检测失败（非致命）: {e}")
        pass

    # 4. 生成文件名
    ext = file.filename.split(".")[-1] if file.filename and "." in file.filename else "webp"
    filename = f"{uuid.uuid4().hex}.{ext}"
    logger.info(f"生成文件名: {filename}")

    # 5. 连接 MinIO
    try:
        client = _get_client()
        logger.info(f"MinIO 客户端创建成功，开始检查 bucket...")
    except Exception as e:
        logger.error(f"创建 MinIO 客户端失败: {e}")
        raise HTTPException(500, f"连接 MinIO 失败: {e}")

    # 6. 确保 bucket 存在
    try:
        _ensure_bucket(client)
    except Exception as e:
        logger.error(f"bucket 操作失败: {e}")
        raise HTTPException(500, f"MinIO bucket 操作失败: {e}")

    # 7. 上传文件
    try:
        logger.info(f"开始上传: bucket={MINIO_BUCKET}, object={filename}, size={len(content)}")
        client.put_object(
            bucket_name=MINIO_BUCKET,
            object_name=filename,
            data=BytesIO(content),
            length=len(content),
            content_type=file.content_type,
        )
        logger.info(f"上传成功: {filename}")
    except Exception as e:
        logger.error(f"MinIO put_object 失败: {e}")
        raise HTTPException(500, f"文件上传失败: {e}")

    # 8. 生成 URL
    url = f"{MINIO_PUBLIC_URL.rstrip('/')}/{filename}"
    logger.info(f"返回图片 URL: {url}")
    return {"url": url, "orientation": orientation}


# 测试接口：排查 MinIO 连接，无需登录
@router.get("/test-minio")
def test_minio():
    logger.info("=== MinIO 连接测试开始 ===")
    try:
        logger.info(f"ENDPOINT={MINIO_ENDPOINT}, BUCKET={MINIO_BUCKET}, SECURE={MINIO_SECURE}, PUBLIC_URL={MINIO_PUBLIC_URL}")
        logger.info(f"ACCESS_KEY={MINIO_ACCESS_KEY[:8]}***, SECRET_KEY={MINIO_SECRET_KEY[:8]}***")
    except Exception:
        pass

    try:
        client = _get_client()
        logger.info("MinIO 客户端创建成功")
    except Exception as e:
        logger.error(f"创建客户端失败: {e}")
        return {"status": "error", "step": "create_client", "detail": str(e)}

    try:
        found = client.bucket_exists(MINIO_BUCKET)
        logger.info(f"bucket_exists = {found}")
    except Exception as e:
        logger.error(f"bucket_exists 失败: {e}")
        return {"status": "error", "step": "bucket_exists", "detail": str(e)}

    try:
        _ensure_bucket(client)
        logger.info("bucket 策略设置成功")
    except Exception as e:
        logger.error(f"设置策略失败: {e}")
        return {"status": "error", "step": "set_policy", "detail": str(e)}

    try:
        test_obj = "test-upload-debug.txt"
        client.put_object(MINIO_BUCKET, test_obj, BytesIO(b"hello minio"), length=10)
        logger.info(f"测试文件上传成功: {test_obj}")
        client.remove_object(MINIO_BUCKET, test_obj)
        logger.info("测试文件删除成功")
    except Exception as e:
        logger.error(f"put_object 失败: {e}")
        return {"status": "error", "step": "put_object", "detail": str(e)}

    logger.info("=== MinIO 全部测试通过 ===")
    return {"status": "ok", "endpoint": MINIO_ENDPOINT, "bucket": MINIO_BUCKET}
