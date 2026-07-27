import httpx
from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/api/music", tags=["音乐"])

METING_BASE = "https://api.injahow.cn/meting/"


def extract_id(url: str):
    import re
    match = re.search(r"id=(\d+)", url)
    return match.group(1) if match else ""


@router.get("")
async def get_music(
    id: str = Query(...)
):

    async with httpx.AsyncClient(timeout=10) as client:

        try:
            resp = await client.get(
                METING_BASE,
                params={
                    "server": "netease",
                    "type": "playlist",
                    "id": id
                }
            )

            tracks = resp.json()

            songs = []

            for track in tracks:

                songs.append({
                    "id": extract_id(track.get("url","")),
                    "title": track.get("name",""),
                    "artist": track.get("artist",""),
                    "cover": track.get("pic",""),
                    "lrcUrl": track.get("lrc",""),

                    # 暂时直接返回url接口
                    "src": track.get("url","")
                })


            return songs


        except Exception as e:
            return JSONResponse(
                {
                    "error": str(e)
                },
                status_code=500
            )