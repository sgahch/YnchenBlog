"""
外部 API 代理 — 替代原 Next.js app/api/uapis/route.ts
将前端的 /api/uapis?path=xxx 代理到 https://uapis.cn/api/v1/{path}
"""
import httpx
from fastapi import APIRouter, Query, Request
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/api/uapis", tags=["外部API"])

UAPIS_BASE = "https://uapis.cn/api/v1"


def build_target(path: str, params: dict) -> str:
    """构造目标 URL，去掉 path 参数后拼接其余查询参数"""
    qs_parts = []
    for k, v in params.items():
        if k != "path":
            qs_parts.append(f"{k}={v}")
    qs = "&".join(qs_parts)
    url = f"{UAPIS_BASE}/{path}"
    if qs:
        url += f"?{qs}"
    return url


@router.get("")
async def proxy_get(request: Request, path: str = Query(..., description="子路径")):
    url = build_target(path, dict(request.query_params))
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(url)
            return JSONResponse(resp.json(), status_code=resp.status_code)
    except Exception as e:
        return JSONResponse({"message": f"请求外部API失败: {str(e)}"}, status_code=502)


@router.post("")
async def proxy_post(request: Request, path: str = Query(..., description="子路径")):
    url = build_target(path, dict(request.query_params))
    try:
        body = await request.json()
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(url, json=body, headers={"Content-Type": "application/json"})
            return JSONResponse(resp.json(), status_code=resp.status_code)
    except Exception as e:
        return JSONResponse({"message": f"请求外部API失败: {str(e)}"}, status_code=502)
