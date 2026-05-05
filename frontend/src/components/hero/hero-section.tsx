"use client";

import dynamic from "next/dynamic";
import { Suspense } from "react";

// Lazy load the 3D component to avoid SSR issues with Three.js
const AgentGraph3D = dynamic(
  () => import("./agent-graph-3d").then((mod) => ({ default: mod.AgentGraph3D })),
  { ssr: false },
);

export function HeroSection() {
  return (
    <Suspense
      fallback={
        <div className="w-full h-[500px] flex items-center justify-center">
          <div className="flex flex-col items-center gap-3">
            <div className="w-10 h-10 border-2 border-[#D4A853] border-t-transparent rounded-full animate-spin" />
            <p className="text-xs text-slate-500">Loading visualization...</p>
          </div>
        </div>
      }
    >
      <AgentGraph3D />
    </Suspense>
  );
}
