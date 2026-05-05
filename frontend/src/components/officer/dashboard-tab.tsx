"use client";

import { useEffect, useState, Fragment } from "react";
import { useSession } from "next-auth/react";
import {
  FileText,
  TrendingUp,
  TrendingDown,
  Brain,
  Timer,
  AlertTriangle,
  ArrowRight,
  ChevronRight,
  UserCheck,
  FileUp,
  ScanSearch,
  Database,
  IndianRupee,
  ShieldAlert,
  Calculator,
  Scale,
} from "lucide-react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface DashboardTabProps {
  onSwitchTab: (tab: string) => void;
}

interface StatsData {
  total_applications: number;
  weekly_change_pct: number;
  monthly_change_pct: number;
  decision_breakdown: {
    approved: number;
    denied: number;
    escalated: number;
    conditional: number;
  };
  ai_confidence_pct: number;
  override_rate_pct: number;
  avg_processing_hours: number;
  processing_change_pct: number;
  pending_review_count: number;
  oldest_pending_minutes: number;
}

interface RecentApp {
  id: string;
  applicant_name: string;
  reference_number: string;
  loan_type: string;
  loan_amount: number;
  status: string;
  decision: string | null;
  created_at: string;
}

const PIPELINE_NODES = [
  { icon: UserCheck, name: "Intake", latency: "2.1s", rate: "99.2%", color: "green" },
  { icon: FileUp, name: "Docs", latency: "1.8s", rate: "98.7%", color: "green" },
  { icon: ScanSearch, name: "Verify", latency: "4.5s", rate: "96.1%", color: "amber" },
  { icon: Database, name: "Bureau", latency: "3.2s", rate: "97.8%", color: "green" },
  { icon: IndianRupee, name: "Income", latency: "2.8s", rate: "98.3%", color: "green" },
  { icon: ShieldAlert, name: "Risk", latency: "3.7s", rate: "99.5%", color: "green" },
  { icon: Calculator, name: "Pricing", latency: "0.8s", rate: "100%", color: "green" },
  { icon: Scale, name: "Decision", latency: "2.3s", rate: "7.3% HITL", color: "gold", active: true },
];

function formatMinutes(mins: number): string {
  if (mins >= 60) {
    const h = Math.floor(mins / 60);
    const m = mins % 60;
    return `${h}h ${m}m`;
  }
  return `${mins}m`;
}

function timeAgo(isoString: string): string {
  const diff = Date.now() - new Date(isoString).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  return `${Math.floor(hrs / 24)}d ago`;
}

function formatINR(amount: number): string {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(amount);
}

function getDecisionColors(decision: string | null): { bg: string; text: string } {
  switch (decision) {
    case "approved":
      return { bg: "#E8F5EE", text: "#1B6B3A" };
    case "denied":
      return { bg: "#FCEAEA", text: "#922020" };
    case "escalated":
      return { bg: "#FDF3E2", text: "#8B5E00" };
    case "conditional":
      return { bg: "#E8F0FE", text: "#1A56B8" };
    default:
      return { bg: "#F5F2EA", text: "#7A7568" };
  }
}

function getInitials(name: string): string {
  const parts = name.trim().split(/\s+/);
  if (parts.length === 1) return (parts[0][0] ?? "?").toUpperCase();
  return (
    (parts[0][0] ?? "").toUpperCase() +
    (parts[parts.length - 1][0] ?? "").toUpperCase()
  );
}

function TrendBadge({ value, label }: { value: number; label: string }) {
  const positive = value >= 0;
  const color = positive ? "#2E8B57" : "#C0392B";
  const TrendIcon = positive ? TrendingUp : TrendingDown;
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 4, marginTop: 2 }}>
      <TrendIcon size={12} color={color} style={{ flexShrink: 0 }} />
      <span style={{ fontSize: 12, fontWeight: 600, color }}>
        {positive ? "+" : ""}{value}%
      </span>
      <span style={{ fontSize: 11, color: "#B0A999" }}>{label}</span>
    </div>
  );
}

export function DashboardTab({ onSwitchTab }: DashboardTabProps) {
  const { data: session } = useSession();
  const [stats, setStats] = useState<StatsData | null>(null);
  const [recentApps, setRecentApps] = useState<RecentApp[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!session) return;
    const token = (session as any)?.backendToken as string;
    const headers = { Authorization: `Bearer ${token}` };

    Promise.all([
      fetch(`${API_URL}/api/v1/admin/stats`, { headers }).then((r) => r.json()),
      fetch(`${API_URL}/api/v1/admin/recent-applications?limit=4`, { headers }).then((r) =>
        r.json()
      ),
    ])
      .then(([s, apps]) => {
        setStats(s);
        setRecentApps(Array.isArray(apps) ? apps : []);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [session]);

  // Placeholder stats for skeleton rendering
  const s = stats ?? {
    total_applications: 0,
    weekly_change_pct: 0,
    monthly_change_pct: 0,
    decision_breakdown: { approved: 0, denied: 0, escalated: 0, conditional: 0 },
    ai_confidence_pct: 0,
    override_rate_pct: 0,
    avg_processing_hours: 0,
    processing_change_pct: 0,
    pending_review_count: 0,
    oldest_pending_minutes: 0,
  };

  // Decision breakdown percentages
  const totalDecisions =
    s.decision_breakdown.approved +
    s.decision_breakdown.denied +
    s.decision_breakdown.escalated +
    s.decision_breakdown.conditional || 1;

  const bars = [
    {
      label: "Approved",
      count: s.decision_breakdown.approved,
      pct: (s.decision_breakdown.approved / totalDecisions) * 100,
      gradient: "linear-gradient(180deg, #2E8B57 0%, #3DAA6D 100%)",
    },
    {
      label: "Denied",
      count: s.decision_breakdown.denied,
      pct: (s.decision_breakdown.denied / totalDecisions) * 100,
      gradient: "linear-gradient(180deg, #C0392B 0%, #E74C3C 100%)",
    },
    {
      label: "Escalated",
      count: s.decision_breakdown.escalated,
      pct: (s.decision_breakdown.escalated / totalDecisions) * 100,
      gradient: "linear-gradient(180deg, #D4860B 0%, #F0A030 100%)",
    },
    {
      label: "Conditional",
      count: s.decision_breakdown.conditional,
      pct: (s.decision_breakdown.conditional / totalDecisions) * 100,
      gradient: "linear-gradient(180deg, #3B7DDD 0%, #5B9CF0 100%)",
    },
  ];

  const maxPct = Math.max(...bars.map((b) => b.pct), 1);
  const CHART_HEIGHT = 140;

  const confidence = s.ai_confidence_pct;
  const circumference = 339.29;

  return (
    <div className="officer-grid">
      {/* ── Row 1 ── */}

      {/* Card 1: Total Applications */}
      <div
        className="officer-card"
        style={{
          gridColumn: "span 4",
          padding: "24px 28px",
          display: "flex",
          flexDirection: "column",
        }}
      >
        {/* Label */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 6,
            fontSize: 11,
            textTransform: "uppercase",
            letterSpacing: "1.2px",
            color: "#B0A999",
            fontWeight: 600,
          }}
        >
          <FileText size={14} style={{ opacity: 0.5 }} />
          Total Applications
        </div>

        {/* Value */}
        <div
          style={{
            fontFamily: "var(--font-dm-serif)",
            fontSize: 44,
            letterSpacing: "-2px",
            lineHeight: 1,
            marginTop: 8,
            color: "#0C1222",
          }}
        >
          {loading ? "—" : s.total_applications.toLocaleString()}
        </div>

        {/* Trends */}
        <div style={{ display: "flex", gap: 20, marginTop: 12 }}>
          <TrendBadge value={s.weekly_change_pct} label="This week" />
          <TrendBadge value={s.monthly_change_pct} label="This month" />
        </div>

        {/* View All button */}
        <button
          onClick={() => onSwitchTab("review")}
          style={{
            marginTop: "auto",
            paddingTop: 20,
            display: "flex",
            alignItems: "center",
            gap: 6,
            background: "#0C1222",
            color: "#fff",
            border: "none",
            borderRadius: 10,
            padding: "10px 16px",
            fontSize: 12,
            fontWeight: 600,
            cursor: "pointer",
            width: "fit-content",
            transition: "opacity 0.2s",
          }}
          onMouseEnter={(e) => (e.currentTarget.style.opacity = "0.85")}
          onMouseLeave={(e) => (e.currentTarget.style.opacity = "1")}
        >
          View All
          <ArrowRight size={13} />
        </button>
      </div>

      {/* Card 2: Decision Breakdown */}
      <div
        className="officer-card"
        style={{ gridColumn: "span 5", padding: "24px 28px" }}
      >
        {/* Header */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            marginBottom: 20,
          }}
        >
          <span
            style={{
              fontSize: 11,
              textTransform: "uppercase",
              letterSpacing: "1.2px",
              color: "#B0A999",
              fontWeight: 600,
            }}
          >
            Decision Breakdown
          </span>
          <span style={{ fontSize: 11, color: "#B0A999" }}>April 2026</span>
        </div>

        {/* Bar chart */}
        <div
          style={{
            display: "flex",
            alignItems: "flex-end",
            gap: 16,
            height: CHART_HEIGHT,
          }}
        >
          {bars.map((bar, i) => {
            const barHeight = (bar.pct / maxPct) * (CHART_HEIGHT - 32);
            return (
              <div
                key={bar.label}
                style={{
                  flex: 1,
                  display: "flex",
                  flexDirection: "column",
                  alignItems: "center",
                  height: "100%",
                  justifyContent: "flex-end",
                }}
              >
                {/* Percentage label */}
                <span
                  style={{
                    fontFamily: "var(--font-jetbrains-mono)",
                    fontSize: 11,
                    fontWeight: 500,
                    color: "#0C1222",
                    marginBottom: 4,
                  }}
                >
                  {bar.pct.toFixed(0)}%
                </span>
                {/* Bar */}
                <div
                  className="bar-grow"
                  style={{
                    width: "100%",
                    height: Math.max(barHeight, 4),
                    background: bar.gradient,
                    borderRadius: "6px 6px 0 0",
                    animationDelay: `${i * 100}ms`,
                  }}
                />
                {/* Category label */}
                <span
                  style={{
                    fontSize: 10,
                    color: "#B0A999",
                    marginTop: 6,
                    textAlign: "center",
                  }}
                >
                  {bar.label}
                </span>
              </div>
            );
          })}
        </div>
      </div>

      {/* Card 3: AI Confidence (gold) */}
      <div
        className="officer-card officer-card-gold"
        style={{
          gridColumn: "span 3",
          padding: "24px 20px",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          position: "relative",
          zIndex: 0,
        }}
      >
        {/* Label */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 6,
            fontSize: 11,
            textTransform: "uppercase",
            letterSpacing: "1.2px",
            color: "rgba(12,18,34,0.6)",
            fontWeight: 600,
            alignSelf: "flex-start",
          }}
        >
          <Brain size={14} style={{ opacity: 0.7 }} />
          AI Confidence
        </div>

        {/* Donut chart */}
        <div style={{ position: "relative", marginTop: 16 }}>
          <svg
            width="130"
            height="130"
            viewBox="0 0 130 130"
            style={{ transform: "rotate(-90deg)" }}
          >
            <circle
              cx="65"
              cy="65"
              r="54"
              fill="none"
              stroke="rgba(12,18,34,0.12)"
              strokeWidth="10"
            />
            <circle
              cx="65"
              cy="65"
              r="54"
              fill="none"
              stroke="#0C1222"
              strokeWidth="10"
              strokeLinecap="round"
              strokeDasharray={`${circumference}`}
              strokeDashoffset={circumference - (circumference * confidence) / 100}
              style={{ animation: "ringFill 1.2s cubic-bezier(0.16,1,0.3,1) 0.3s both" }}
            />
          </svg>
          {/* Center text overlay */}
          <div
            style={{
              position: "absolute",
              inset: 0,
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            <span
              style={{
                fontFamily: "var(--font-dm-serif)",
                fontSize: 34,
                color: "#0C1222",
                lineHeight: 1,
              }}
            >
              {loading ? "—" : `${confidence}%`}
            </span>
            <span
              style={{
                fontSize: 10,
                color: "rgba(12,18,34,0.6)",
                marginTop: 2,
              }}
            >
              accuracy
            </span>
          </div>
        </div>

        {/* Footer */}
        <p
          style={{
            fontSize: 12,
            fontWeight: 600,
            color: "#0C1222",
            opacity: 0.7,
            marginTop: 12,
            textAlign: "center",
          }}
        >
          {s.override_rate_pct}% officer override rate
        </p>
      </div>

      {/* ── Row 2 ── */}

      {/* Card 4: Avg Processing Time (navy) */}
      <div
        className="officer-card officer-card-navy"
        style={{
          gridColumn: "span 3",
          padding: "24px 24px",
          display: "flex",
          flexDirection: "column",
          zIndex: 0,
        }}
      >
        {/* Label */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 6,
            fontSize: 11,
            textTransform: "uppercase",
            letterSpacing: "1.2px",
            color: "rgba(255,255,255,0.5)",
            fontWeight: 600,
          }}
        >
          <Timer size={14} color="#C8A24E" />
          Avg Processing
        </div>

        {/* Value */}
        <div
          style={{
            display: "flex",
            alignItems: "baseline",
            gap: 4,
            marginTop: 12,
          }}
        >
          <span
            style={{
              fontFamily: "var(--font-dm-serif)",
              fontSize: 52,
              color: "#fff",
              lineHeight: 1,
            }}
          >
            {loading ? "—" : s.avg_processing_hours}
          </span>
          <span
            style={{
              fontFamily: "var(--font-dm-sans)",
              fontSize: 20,
              fontWeight: 400,
              color: "rgba(255,255,255,0.7)",
            }}
          >
            h
          </span>
        </div>

        {/* Trend */}
        <div
          style={{ display: "flex", alignItems: "center", gap: 4, marginTop: 8 }}
        >
          <TrendingDown size={12} color="#C8A24E" />
          <span style={{ fontSize: 12, fontWeight: 600, color: "#C8A24E" }}>
            {Math.abs(s.processing_change_pct)}% faster
          </span>
        </div>
        <span style={{ fontSize: 11, color: "#64748b", marginTop: 2 }}>
          vs last month
        </span>
      </div>

      {/* Card 5: Pending Reviews (alert) */}
      <div
        className="officer-card officer-card-alert"
        style={{
          gridColumn: "span 3",
          padding: "24px 24px",
          display: "flex",
          flexDirection: "column",
        }}
      >
        <AlertTriangle size={28} color="#D4860B" />

        <div
          style={{
            fontFamily: "var(--font-dm-serif)",
            fontSize: 22,
            color: "#D4860B",
            marginTop: 10,
            lineHeight: 1,
          }}
        >
          {loading ? "—" : `${s.pending_review_count} Pending`}
        </div>

        <p style={{ fontSize: 12, color: "#7A7568", marginTop: 4 }}>
          Applications awaiting review
        </p>

        <div
          style={{
            fontFamily: "var(--font-jetbrains-mono)",
            fontSize: 11,
            color: "#D4860B",
            marginTop: 8,
          }}
        >
          Oldest: {formatMinutes(s.oldest_pending_minutes)} ago
        </div>

        <button
          onClick={() => onSwitchTab("review")}
          style={{
            marginTop: 16,
            display: "flex",
            alignItems: "center",
            gap: 6,
            background: "#D4860B",
            color: "#fff",
            border: "none",
            borderRadius: 10,
            padding: "10px 16px",
            fontSize: 12,
            fontWeight: 600,
            cursor: "pointer",
            width: "fit-content",
            transition: "opacity 0.2s",
          }}
          onMouseEnter={(e) => (e.currentTarget.style.opacity = "0.85")}
          onMouseLeave={(e) => (e.currentTarget.style.opacity = "1")}
        >
          Review Now
          <ArrowRight size={13} />
        </button>
      </div>

      {/* Card 6: Recent Applications */}
      <div
        className="officer-card"
        style={{ gridColumn: "span 6", padding: "24px 24px" }}
      >
        {/* Section header */}
        <div
          style={{
            display: "flex",
            alignItems: "flex-start",
            justifyContent: "space-between",
            marginBottom: 16,
          }}
        >
          <div>
            <div
              style={{
                fontFamily: "var(--font-dm-serif)",
                fontSize: 17,
                color: "#0C1222",
                lineHeight: 1,
              }}
            >
              Recent Applications
            </div>
            <div style={{ fontSize: 12, color: "#7A7568", marginTop: 3 }}>
              Latest loan submissions
            </div>
          </div>
          <button
            onClick={() => onSwitchTab("review")}
            style={{
              fontSize: 12,
              fontWeight: 600,
              color: "#0C1222",
              background: "#F5F2EA",
              border: "none",
              borderRadius: 20,
              padding: "6px 14px",
              cursor: "pointer",
              transition: "background 0.2s",
            }}
            onMouseEnter={(e) =>
              (e.currentTarget.style.background = "#E8E2D6")
            }
            onMouseLeave={(e) =>
              (e.currentTarget.style.background = "#F5F2EA")
            }
          >
            View all
          </button>
        </div>

        {/* App rows */}
        <div>
          {loading && (
            <div
              style={{
                textAlign: "center",
                padding: "24px 0",
                color: "#B0A999",
                fontSize: 13,
              }}
            >
              Loading…
            </div>
          )}
          {!loading && recentApps.length === 0 && (
            <div
              style={{
                textAlign: "center",
                padding: "24px 0",
                color: "#B0A999",
                fontSize: 13,
              }}
            >
              No recent applications
            </div>
          )}
          {recentApps.map((app, idx) => {
            const { bg, text } = getDecisionColors(app.decision);
            const initials = getInitials(app.applicant_name);
            const isLast = idx === recentApps.length - 1;
            return (
              <div
                key={app.id}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 14,
                  padding: "13px 0",
                  borderBottom: isLast ? "none" : "1px solid rgba(12,18,34,0.06)",
                  transition: "padding-left 0.2s",
                  cursor: "pointer",
                }}
                onMouseEnter={(e) => {
                  (e.currentTarget as HTMLDivElement).style.paddingLeft = "4px";
                  const avatar = (e.currentTarget as HTMLDivElement).querySelector<HTMLDivElement>(
                    "[data-avatar]"
                  );
                  if (avatar) avatar.style.transform = "scale(1.06)";
                }}
                onMouseLeave={(e) => {
                  (e.currentTarget as HTMLDivElement).style.paddingLeft = "0px";
                  const avatar = (e.currentTarget as HTMLDivElement).querySelector<HTMLDivElement>(
                    "[data-avatar]"
                  );
                  if (avatar) avatar.style.transform = "scale(1)";
                }}
              >
                {/* Avatar */}
                <div
                  data-avatar=""
                  style={{
                    width: 42,
                    height: 42,
                    borderRadius: 12,
                    background: bg,
                    color: text,
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    fontSize: 14,
                    fontWeight: 700,
                    flexShrink: 0,
                    transition: "transform 0.2s",
                  }}
                >
                  {initials}
                </div>

                {/* Name + ref */}
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div
                    style={{
                      fontSize: 14,
                      fontWeight: 600,
                      color: "#0C1222",
                      whiteSpace: "nowrap",
                      overflow: "hidden",
                      textOverflow: "ellipsis",
                    }}
                  >
                    {app.applicant_name}
                  </div>
                  <div
                    style={{
                      fontFamily: "var(--font-jetbrains-mono)",
                      fontSize: 11,
                      color: "#B0A999",
                      marginTop: 2,
                      whiteSpace: "nowrap",
                      overflow: "hidden",
                      textOverflow: "ellipsis",
                    }}
                  >
                    {app.reference_number} · {app.loan_type} · {timeAgo(app.created_at)}
                  </div>
                </div>

                {/* Amount */}
                <div
                  style={{
                    fontFamily: "var(--font-dm-serif)",
                    fontSize: 16,
                    color: "#0C1222",
                    flexShrink: 0,
                  }}
                >
                  {formatINR(app.loan_amount)}
                </div>

                {/* Status badge */}
                <span
                  className={`status-badge badge-${app.decision ?? "pending"}`}
                  style={{ flexShrink: 0 }}
                >
                  {app.decision ?? app.status}
                </span>

                {/* Chevron */}
                <div
                  style={{
                    width: 32,
                    height: 32,
                    borderRadius: 8,
                    background: "#F5F2EA",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    flexShrink: 0,
                  }}
                >
                  <ChevronRight size={14} color="#B0A999" />
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* ── Row 3: Agent Pipeline ── */}
      <div
        className="officer-card"
        style={{ gridColumn: "span 12", padding: "24px 28px" }}
      >
        {/* Section header */}
        <div
          style={{
            display: "flex",
            alignItems: "flex-start",
            justifyContent: "space-between",
            marginBottom: 20,
          }}
        >
          <div>
            <div
              style={{
                fontFamily: "var(--font-dm-serif)",
                fontSize: 17,
                color: "#0C1222",
                lineHeight: 1,
              }}
            >
              Agent Pipeline
            </div>
            <div style={{ fontSize: 12, color: "#7A7568", marginTop: 3 }}>
              13 AI agents processing each application
            </div>
          </div>
          <button
            onClick={() => onSwitchTab("settings")}
            style={{
              fontSize: 12,
              fontWeight: 600,
              color: "#0C1222",
              background: "#F5F2EA",
              border: "none",
              borderRadius: 20,
              padding: "6px 14px",
              cursor: "pointer",
              transition: "background 0.2s",
            }}
            onMouseEnter={(e) =>
              (e.currentTarget.style.background = "#E8E2D6")
            }
            onMouseLeave={(e) =>
              (e.currentTarget.style.background = "#F5F2EA")
            }
          >
            Configure
          </button>
        </div>

        {/* Pipeline nodes */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 4,
            overflowX: "auto",
            paddingBottom: 4,
          }}
        >
          {PIPELINE_NODES.map((node, i) => {
            const Icon = node.icon;
            const isActive = node.active;
            const rateColor =
              node.color === "gold"
                ? "#C8A24E"
                : node.color === "amber"
                ? "#D4860B"
                : "#2E8B57";

            return (
              <Fragment key={node.name}>
                <div
                  className="pipeline-node"
                  style={{
                    minWidth: 110,
                    padding: 14,
                    background: isActive ? "#0C1222" : "#F5F2EA",
                    borderRadius: 14,
                    textAlign: "center",
                    display: "flex",
                    flexDirection: "column",
                    alignItems: "center",
                    gap: 4,
                    animationDelay: `${i * 50}ms`,
                    flexShrink: 0,
                  }}
                >
                  <Icon
                    size={22}
                    color={isActive ? "#C8A24E" : "#7A7568"}
                  />
                  <span
                    style={{
                      fontSize: 11,
                      fontWeight: 600,
                      color: isActive ? "#fff" : "#0C1222",
                    }}
                  >
                    {node.name}
                  </span>
                  <span
                    style={{
                      fontFamily: "var(--font-jetbrains-mono)",
                      fontSize: 16,
                      color: isActive ? "rgba(255,255,255,0.8)" : "#0C1222",
                    }}
                  >
                    {node.latency}
                  </span>
                  <span
                    style={{
                      fontSize: 10,
                      fontWeight: 600,
                      color: rateColor,
                    }}
                  >
                    {node.rate}
                  </span>
                </div>
                {i < PIPELINE_NODES.length - 1 && (
                  <span
                    style={{
                      fontSize: 14,
                      color: "#B0A999",
                      opacity: 0.3,
                      flexShrink: 0,
                    }}
                  >
                    →
                  </span>
                )}
              </Fragment>
            );
          })}
        </div>
      </div>
    </div>
  );
}
