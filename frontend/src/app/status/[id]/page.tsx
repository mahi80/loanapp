"use client";

import { useParams } from "next/navigation";
import { ApplicationDetail } from "@/components/status/application-detail";

export default function StatusDetailPage() {
  const { id } = useParams();
  return (
    <div className="flex-1 overflow-auto p-6">
      <div className="max-w-3xl mx-auto">
        <ApplicationDetail applicationId={id as string} />
      </div>
    </div>
  );
}
