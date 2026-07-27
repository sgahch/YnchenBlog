"use client";

import dynamic from "next/dynamic";

const MarkdownEditor = dynamic(() => import("./MarkdownEditor"), {
  ssr: false,
  loading: () => (
    <div className="flex items-center justify-center min-h-[60vh]">
      <div className="w-8 h-8 border-2 border-sky-500 border-t-transparent rounded-full animate-spin" />
    </div>
  ),
});

export default function MarkdownPage() {
  return <MarkdownEditor />;
}
