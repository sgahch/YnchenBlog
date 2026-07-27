"use client";

import dynamic from "next/dynamic";

const StudioCanvas = dynamic(() => import("./StudioCanvas"), {
  ssr: false,
  loading: () => (
    <div className="flex items-center justify-center min-h-screen">
      <div className="w-8 h-8 border-2 border-amber-600 border-t-transparent rounded-full animate-spin" />
    </div>
  ),
});

export default function StudioPage() {
  return <StudioCanvas />;
}
