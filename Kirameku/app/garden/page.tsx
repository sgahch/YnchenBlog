"use client";

import dynamic from "next/dynamic";

const GardenDashboard = dynamic(() => import("./GardenDashboard"), {
  ssr: false,
  loading: () => (
    <div className="flex items-center justify-center min-h-[60vh]">
      <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
    </div>
  ),
});

export default function GardenPage() {
  return <GardenDashboard />;
}
