"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import { useSession } from "next-auth/react";
import { useRouter } from "next/navigation";
import { Bell, CheckCircle2, XCircle, AlertCircle } from "lucide-react";
import { apiClient } from "@/lib/api";

interface NotificationData {
  application_id: string;
  reference_number: string | null;
  decision: string;
  decision_label: string;
  message: string;
  reviewed_at: string;
}

const POLL_INTERVAL_MS = 30_000;

function decisionIcon(decision: string) {
  const d = decision.toLowerCase();
  if (d.includes("approve")) return <CheckCircle2 className="h-4 w-4 text-green-500 shrink-0" />;
  if (d.includes("reject") || d.includes("deny")) return <XCircle className="h-4 w-4 text-red-500 shrink-0" />;
  return <AlertCircle className="h-4 w-4 text-amber-500 shrink-0" />;
}

function formatRelative(iso: string) {
  try {
    const diff = Date.now() - new Date(iso).getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 1) return "just now";
    if (mins < 60) return `${mins}m ago`;
    const hrs = Math.floor(mins / 60);
    if (hrs < 24) return `${hrs}h ago`;
    return `${Math.floor(hrs / 24)}d ago`;
  } catch {
    return "";
  }
}

export function NotificationBell() {
  const { data: session } = useSession();
  const router = useRouter();
  const [items, setItems] = useState<NotificationData[]>([]);
  const [open, setOpen] = useState(false);
  const wrapRef = useRef<HTMLDivElement>(null);

  const fetchNotifications = useCallback(async () => {
    if (!session) return;
    const token = (session as any)?.backendToken as string;
    if (!token) return;
    try {
      const data: NotificationData[] = await apiClient("/api/v1/notifications", { token });
      setItems(Array.isArray(data) ? data : []);
    } catch {
      // Silently ignore fetch errors — bell just shows stale count
    }
  }, [session]);

  useEffect(() => {
    fetchNotifications();
    const interval = setInterval(fetchNotifications, POLL_INTERVAL_MS);
    return () => clearInterval(interval);
  }, [fetchNotifications]);

  // Close on outside click
  useEffect(() => {
    if (!open) return;
    const onClick = (e: MouseEvent) => {
      if (wrapRef.current && !wrapRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", onClick);
    return () => document.removeEventListener("mousedown", onClick);
  }, [open]);

  // Close on Escape
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => { if (e.key === "Escape") setOpen(false); };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [open]);

  const count = items.length;

  const handleItemClick = (applicationId: string) => {
    setOpen(false);
    router.push(`/status?application=${applicationId}`);
  };

  return (
    <div ref={wrapRef} className="relative">
      <button
        onClick={() => setOpen((v) => !v)}
        className="relative p-2 rounded-lg hover:bg-slate-100 transition-colors focus:outline-none focus:ring-2 focus:ring-[#D4A853]/40"
        aria-label={count > 0 ? `${count} new notifications` : "No new notifications"}
        aria-expanded={open}
        aria-haspopup="true"
      >
        <Bell className="h-5 w-5 text-slate-500" />
        {count > 0 && (
          <span className="absolute -top-0.5 -right-0.5 flex items-center justify-center rounded-full bg-red-500 text-[10px] font-bold text-white ring-2 ring-white min-w-[18px] h-[18px] px-1">
            {count > 99 ? "99+" : count}
          </span>
        )}
      </button>

      {open && (
        <div
          role="dialog"
          aria-label="Notifications"
          className="absolute right-0 mt-2 w-80 max-w-[calc(100vw-2rem)] bg-white rounded-xl shadow-xl border border-slate-200 z-50 overflow-hidden"
        >
          <div className="px-4 py-3 border-b border-slate-100 flex items-center justify-between">
            <h3 className="text-sm font-semibold text-[#0F172A]">Notifications</h3>
            {count > 0 && (
              <span className="text-xs text-slate-400">{count} new</span>
            )}
          </div>

          <div className="max-h-96 overflow-y-auto">
            {count === 0 ? (
              <div className="py-10 text-center text-sm text-slate-400">
                You&apos;re all caught up.
              </div>
            ) : (
              <ul className="divide-y divide-slate-100">
                {items.map((n) => (
                  <li key={n.application_id}>
                    <button
                      onClick={() => handleItemClick(n.application_id)}
                      className="w-full text-left px-4 py-3 hover:bg-slate-50 transition-colors flex gap-3"
                    >
                      {decisionIcon(n.decision)}
                      <div className="min-w-0 flex-1">
                        <p className="text-sm font-medium text-[#0F172A] truncate">
                          {n.decision_label || n.decision}
                          {n.reference_number && (
                            <span className="ml-2 text-xs text-slate-400 font-normal">
                              {n.reference_number}
                            </span>
                          )}
                        </p>
                        <p className="text-xs text-slate-500 mt-0.5 line-clamp-2">
                          {n.message}
                        </p>
                        <p className="text-[10px] text-slate-400 mt-1">
                          {formatRelative(n.reviewed_at)}
                        </p>
                      </div>
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>

          <div className="border-t border-slate-100 px-4 py-2">
            <button
              onClick={() => { setOpen(false); router.push("/status"); }}
              className="w-full text-center text-xs text-slate-500 hover:text-[#0F172A] transition-colors py-1"
            >
              View all applications
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
