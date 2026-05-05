"use client";

import { useState, useEffect } from "react";
import { useSession } from "next-auth/react";
import { OfficerTopbar } from "@/components/officer/officer-topbar";
import { DashboardTab } from "@/components/officer/dashboard-tab";
import { ReviewTab } from "@/components/officer/review-tab";
import { SettingsTab } from "@/components/officer/settings-tab";
import { AnalyticsTab } from "@/components/officer/analytics-tab";
import "@/components/officer/officer.css";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function DashboardPage() {
  const { data: session } = useSession();
  const [activeTab, setActiveTab] = useState("dashboard");
  const [pendingCount, setPendingCount] = useState(0);

  // Fetch pending review count for badge
  useEffect(() => {
    if (!session) return;
    const token = (session as any)?.backendToken as string;
    fetch(`${API_URL}/api/v1/admin/stats`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((r) => r.json())
      .then((data) => setPendingCount(data.pending_review_count || 0))
      .catch(() => {});
  }, [session]);

  return (
    <div className="officer-dashboard min-h-screen">
      <OfficerTopbar
        activeTab={activeTab}
        onTabChange={setActiveTab}
        pendingCount={pendingCount}
        userName={session?.user?.name}
      />

      <main className="p-4 pb-10" key={activeTab}>
        {activeTab === "dashboard" && (
          <DashboardTab onSwitchTab={setActiveTab} />
        )}
        {activeTab === "review" && <ReviewTab />}
        {activeTab === "settings" && <SettingsTab />}
        {activeTab === "analytics" && <AnalyticsTab />}
      </main>
    </div>
  );
}
