import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // 静态导出模式 — 生成 out/ 目录，类似 Vue 的 dist/
  output: "export",

  compress: true,

  // rewrites 仅 dev 模式生效；生产环境由 Nginx 处理反代
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: "http://127.0.0.1:6789/api/:path*",
      },
      {
        source: "/uploads/:path*",
        destination: "http://127.0.0.1:6789/uploads/:path*",
      },
    ];
  },

  experimental: {
    optimizePackageImports: [
      "framer-motion",
      "lucide-react",
    ],
  },

  // 静态导出下远程图片无法服务端优化，统一关闭
  images: {
    unoptimized: true,
  },
};

export default nextConfig;
