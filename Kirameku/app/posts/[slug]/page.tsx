import { postsData } from "@/data/posts";
import PostDetailClient from "./PostDetailClient";

// 静态导出：预生成所有已发布文章的静态 HTML
// 优先从后端 API 获取 slug，后端不可用时回退到本地数据源
export async function generateStaticParams() {
  const slugs = new Set<string>();

  // 1. 尝试从后端获取（需要后端可访问）
  try {
    const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:6789";
    const res = await fetch(`${API}/api/posts?status=published&size=200`, {
      signal: AbortSignal.timeout(5000),
    });
    if (res.ok) {
      const posts: { slug: string }[] = await res.json();
      posts.forEach((p) => slugs.add(p.slug));
    }
  } catch {
    // 后端不可用，使用本地数据源
  }

  // 2. 回退：从本地数据文件获取已知 slug
  if (slugs.size === 0) {
    postsData.forEach((p) => slugs.add(p.slug));
  }

  // 3. 至少需要一个占位，防止构建失败
  if (slugs.size === 0) {
    slugs.add("placeholder");
  }

  return Array.from(slugs).map((slug) => ({ slug }));
}

export default function PostDetailPage() {
  return <PostDetailClient />;
}
