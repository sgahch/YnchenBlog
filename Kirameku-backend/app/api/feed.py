"""
RSS Feed 生成 — 替代原 Next.js app/feed/route.ts
直接从数据库查询已发布文章，生成标准 RSS 2.0 XML
"""
from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlmodel import Session, select

from app.deps import get_session
from app.models import Post, Category

router = APIRouter(tags=["RSS"])

SITE_TITLE = "Ynchen. ~の小站"
SITE_URL = "https://hq-ynchen.xyz"
SITE_DESCRIPTION = "项目开源在 GitHub, 欢迎 star 和 fork！(◕‿◕)"
AUTHOR_EMAIL = "guh982719@gmail.com"


def escape_xml(text: str) -> str:
    """转义 XML 特殊字符"""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )


def format_rfc2822(dt: datetime | None) -> str:
    """将 datetime 转为 RFC 2822 格式"""
    if dt is None:
        return ""
    # 确保有时区信息
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.strftime("%a, %d %b %Y %H:%M:%S %z")


def markdown_to_html(md: str) -> str:
    """简单的 Markdown → HTML 转换（无需外部依赖）"""
    try:
        import markdown
        return markdown.markdown(md, extensions=["fenced_code", "codehilite"])
    except ImportError:
        # 回退：至少转义 XML 并用 <pre> 包裹
        return f"<pre>{escape_xml(md)}</pre>"


@router.get("/feed")
def rss_feed(session: Session = Depends(get_session)):
    # 获取最近 10 篇已发布文章
    q = (
        select(Post)
        .where(Post.status == "published")
        .order_by(Post.is_pinned.desc(), Post.published_at.desc(), Post.created_at.desc())
        .limit(10)
    )
    posts = session.exec(q).all()

    items = []
    for post in posts:
        post_url = f"{SITE_URL}/posts/{post.slug}"
        pub_date = post.published_at if post.published_at else post.created_at
        rfc_date = format_rfc2822(pub_date)

        # 分类标签
        tags = []
        # 通过 service 拿标签（避免循环导入，直接在这里查）
        from app.models import PostTag, Tag
        tag_names = []
        pts = session.exec(
            select(PostTag).where(PostTag.post_id == post.id)
        ).all()
        for pt in pts:
            tag = session.get(Tag, pt.tag_id)
            if tag:
                tag_names.append(tag.name)

        categories_xml = "\n".join(
            f"      <category>{escape_xml(t)}</category>" for t in tag_names
        )

        # Markdown → HTML
        content_html = markdown_to_html(post.content or "")

        description = escape_xml(post.description or "")
        title_escaped = escape_xml(post.title)

        items.append(f"""    <item>
      <title><![CDATA[{post.title}]]></title>
      <link>{post_url}</link>
      <guid isPermaLink="true">{post_url}</guid>
      <description><![CDATA[{description}]]></description>
      <content:encoded><![CDATA[{content_html}]]></content:encoded>
      <pubDate>{rfc_date}</pubDate>
      <author>{escape_xml(AUTHOR_EMAIL)}</author>{f"{chr(10)}{categories_xml}" if categories_xml else ""}
    </item>""")

    items_xml = "\n".join(items)
    now_rfc = format_rfc2822(datetime.now(timezone.utc))

    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom" xmlns:content="http://purl.org/rss/1.0/modules/content/">
  <channel>
    <title>{escape_xml(SITE_TITLE)}</title>
    <link>{SITE_URL}</link>
    <description>{escape_xml(SITE_DESCRIPTION)}</description>
    <language>zh-CN</language>
    <lastBuildDate>{now_rfc}</lastBuildDate>
    <atom:link href="{SITE_URL}/feed" rel="self" type="application/rss+xml"/>
    <generator>FastAPI</generator>
{items_xml}
  </channel>
</rss>"""

    return Response(content=xml, media_type="application/rss+xml; charset=utf-8")
