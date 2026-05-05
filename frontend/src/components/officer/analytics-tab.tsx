"use client";

import { useEffect, useState } from "react";
import { useSession } from "next-auth/react";
import { TrendingUp, ShieldCheck, type LucideIcon } from "lucide-react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/* ── Types ── */

interface WeekData {
  week: string;
  approved: number;
  denied: number;
  escalated: number;
  conditional: number;
}

interface RiskBucket {
  range: string;
  category: "low" | "medium" | "high" | "very_high";
  count: number;
}

interface AuditEntry {
  application_id: string;
  applicant_name: string;
  ai_decision: string;
  officer_decision: string | null;
  is_override: boolean;
  confidence: number;
  notes: string | null;
  decided_at: string;
}

/* ── Helpers ── */

function formatDate(iso: string): string {
  const d = new Date(iso);
  const day = String(d.getDate()).padStart(2, "0");
  const months = [
    "Jan","Feb","Mar","Apr","May","Jun",
    "Jul","Aug","Sep","Oct","Nov","Dec",
  ];
  const month = months[d.getMonth()];
  const year = d.getFullYear();
  return `${day} ${month} ${year}`;
}

function shortenWeek(week: string): string {
  // "2026-W11" → "W11"
  const parts = week.split("-");
  return parts[1] ?? week;
}

function decisionBadgeClass(decision: string): string {
  switch (decision) {
    case "approved":    return "badge-approved";
    case "denied":      return "badge-denied";
    case "escalated":   return "badge-escalated";
    case "conditional": return "badge-conditional";
    default:            return "badge-escalated";
  }
}

function riskColor(category: string): string {
  switch (category) {
    case "low":       return "#2E8B57";
    case "medium":    return "#D4860B";
    case "high":      return "#C0392B";
    case "very_high": return "#922020";
    default:          return "#B0A999";
  }
}

/* ── Sub-components ── */

function CardHeader({
  title,
  subtitle,
}: {
  title: string;
  subtitle: string;
}) {
  return (
    <div style={{ marginBottom: 16 }}>
      <div
        style={{
          fontFamily: "var(--font-dm-serif)",
          fontSize: 16,
          color: "#0C1222",
          lineHeight: 1,
        }}
      >
        {title}
      </div>
      <div style={{ fontSize: 11, color: "#B0A999", marginTop: 4 }}>
        {subtitle}
      </div>
    </div>
  );
}

function EmptyPlaceholder({
  icon: Icon,
  label,
}: {
  icon: LucideIcon;
  label: string;
}) {
  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        height: 180,
        gap: 10,
        color: "#B0A999",
      }}
    >
      <Icon size={40} style={{ opacity: 0.3 }} />
      <span style={{ fontSize: 13 }}>{label}</span>
    </div>
  );
}

/* ── Main Component ── */

export function AnalyticsTab() {
  const { data: session } = useSession();
  const [trends, setTrends] = useState<WeekData[]>([]);
  const [riskBuckets, setRiskBuckets] = useState<RiskBucket[]>([]);
  const [auditTrail, setAuditTrail] = useState<AuditEntry[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!session) return;
    const token = (session as any)?.backendToken as string;
    const headers = { Authorization: `Bearer ${token}` };

    Promise.all([
      fetch(`${API_URL}/api/v1/admin/analytics/trends?weeks=8`, { headers })
        .then((r) => r.json())
        .then((d) => (Array.isArray(d?.weeks) ? d.weeks : []))
        .catch(() => []),
      fetch(`${API_URL}/api/v1/admin/analytics/risk-distribution`, { headers })
        .then((r) => r.json())
        .then((d) => (Array.isArray(d?.buckets) ? d.buckets : []))
        .catch(() => []),
      fetch(`${API_URL}/api/v1/admin/analytics/audit-trail?limit=20`, { headers })
        .then((r) => r.json())
        .then((d) => (Array.isArray(d) ? d : []))
        .catch(() => []),
    ])
      .then(([t, r, a]) => {
        setTrends(t);
        setRiskBuckets(r);
        setAuditTrail(a);
      })
      .finally(() => setLoading(false));
  }, [session]);

  /* Detect "all zeros" for trends */
  const trendsEmpty =
    trends.length === 0 ||
    trends.every(
      (w) => w.approved === 0 && w.denied === 0 && w.escalated === 0 && w.conditional === 0
    );

  const riskEmpty = riskBuckets.length === 0 || riskBuckets.every((b) => b.count === 0);

  /* Recharts data shapes */
  const trendsData = trends.map((w) => ({
    ...w,
    name: shortenWeek(w.week),
  }));

  const riskData = riskBuckets.map((b) => ({
    name: b.range,
    count: b.count,
    category: b.category,
  }));

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
      {/* ── Page Header ── */}
      <div style={{ marginBottom: 4 }}>
        <div
          style={{
            fontFamily: "var(--font-dm-serif)",
            fontSize: 24,
            color: "#0C1222",
            lineHeight: 1,
          }}
        >
          Analytics
        </div>
        <div style={{ fontSize: 13, color: "#B0A999", marginTop: 6 }}>
          Performance insights and decision audit trail
        </div>
      </div>

      {/* ── Row 1: Charts ── */}
      <div className="officer-grid">
        {/* Approval Trends */}
        <div
          className="officer-card"
          style={{ gridColumn: "span 6", padding: 24, minHeight: 260 }}
        >
          <CardHeader title="Approval Trends" subtitle="Weekly decisions" />

          {loading ? (
            <div style={{ height: 180 }} />
          ) : trendsEmpty ? (
            <EmptyPlaceholder icon={TrendingUp} label="No trend data yet" />
          ) : (
            <ResponsiveContainer width="100%" height={180}>
              <BarChart
                data={trendsData}
                margin={{ top: 0, right: 0, left: -20, bottom: 0 }}
              >
                <CartesianGrid vertical={false} stroke="#E8E2D6" />
                <XAxis
                  dataKey="name"
                  tick={{ fontSize: 11, fill: "#B0A999" }}
                  axisLine={false}
                  tickLine={false}
                />
                <YAxis
                  tick={{ fontSize: 11, fill: "#B0A999" }}
                  axisLine={false}
                  tickLine={false}
                  allowDecimals={false}
                />
                <Tooltip
                  contentStyle={{
                    background: "#FFFDF8",
                    border: "1px solid rgba(12,18,34,0.06)",
                    borderRadius: 10,
                    fontSize: 12,
                  }}
                  itemStyle={{ color: "#0C1222" }}
                  labelStyle={{ color: "#B0A999", fontWeight: 600 }}
                />
                <Bar dataKey="approved" stackId="a" fill="#2E8B57" radius={[0, 0, 0, 0]} name="Approved" />
                <Bar dataKey="denied" stackId="a" fill="#C0392B" radius={[0, 0, 0, 0]} name="Denied" />
                <Bar dataKey="escalated" stackId="a" fill="#D4860B" radius={[0, 0, 0, 0]} name="Escalated" />
                <Bar dataKey="conditional" stackId="a" fill="#3B7DDD" radius={[4, 4, 0, 0]} name="Conditional" />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Risk Distribution */}
        <div
          className="officer-card"
          style={{ gridColumn: "span 6", padding: 24, minHeight: 260 }}
        >
          <CardHeader title="Risk Distribution" subtitle="Score buckets" />

          {loading ? (
            <div style={{ height: 180 }} />
          ) : riskEmpty ? (
            <EmptyPlaceholder icon={TrendingUp} label="No distribution data yet" />
          ) : (
            <ResponsiveContainer width="100%" height={180}>
              <BarChart
                data={riskData}
                layout="vertical"
                margin={{ top: 0, right: 40, left: 0, bottom: 0 }}
              >
                <XAxis type="number" hide />
                <YAxis
                  type="category"
                  dataKey="name"
                  tick={{ fontSize: 11, fill: "#B0A999" }}
                  axisLine={false}
                  tickLine={false}
                  width={70}
                />
                <Tooltip
                  contentStyle={{
                    background: "#FFFDF8",
                    border: "1px solid rgba(12,18,34,0.06)",
                    borderRadius: 10,
                    fontSize: 12,
                  }}
                  itemStyle={{ color: "#0C1222" }}
                  labelStyle={{ color: "#B0A999", fontWeight: 600 }}
                  formatter={(value) => [value, "Count"]}
                />
                <Bar dataKey="count" name="Count" radius={[0, 4, 4, 0]} label={{ position: "right", fontSize: 11, fill: "#7A7568" }}>
                  {riskData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={riskColor(entry.category)} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      {/* ── Row 2: Audit Trail ── */}
      <div className="officer-card" style={{ padding: 24 }}>
        <CardHeader title="Decision Audit Trail" subtitle="AI vs officer decisions" />

        {loading ? (
          <div style={{ textAlign: "center", padding: "32px 0", color: "#B0A999", fontSize: 13 }}>
            Loading…
          </div>
        ) : auditTrail.length === 0 ? (
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              justifyContent: "center",
              padding: "48px 0",
              gap: 10,
              color: "#B0A999",
            }}
          >
            <ShieldCheck size={40} style={{ opacity: 0.3 }} />
            <span style={{ fontSize: 13 }}>No decisions yet</span>
          </div>
        ) : (
          <div style={{ overflowX: "auto" }}>
            <table className="officer-table">
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Applicant</th>
                  <th>AI Decision</th>
                  <th>Officer Decision</th>
                  <th>Override?</th>
                  <th>Confidence</th>
                  <th>Notes</th>
                </tr>
              </thead>
              <tbody>
                {auditTrail.map((entry) => (
                  <tr key={entry.application_id}>
                    {/* Date */}
                    <td>
                      <span
                        style={{
                          fontFamily: "var(--font-jetbrains-mono)",
                          fontSize: 12,
                          color: "#7A7568",
                        }}
                      >
                        {formatDate(entry.decided_at)}
                      </span>
                    </td>

                    {/* Applicant */}
                    <td>
                      <span style={{ fontSize: 13, fontWeight: 500, color: "#0C1222" }}>
                        {entry.applicant_name}
                      </span>
                    </td>

                    {/* AI Decision */}
                    <td>
                      <span className={`status-badge ${decisionBadgeClass(entry.ai_decision)}`}>
                        {entry.ai_decision}
                      </span>
                    </td>

                    {/* Officer Decision */}
                    <td>
                      {entry.officer_decision ? (
                        <span className={`status-badge ${decisionBadgeClass(entry.officer_decision)}`}>
                          {entry.officer_decision}
                        </span>
                      ) : (
                        <span style={{ color: "#B0A999" }}>—</span>
                      )}
                    </td>

                    {/* Override? */}
                    <td>
                      {entry.is_override ? (
                        <span
                          style={{
                            display: "inline-block",
                            background: "#FEFCE8",
                            color: "#92400E",
                            fontWeight: 600,
                            fontSize: 11,
                            padding: "3px 10px",
                            borderRadius: 20,
                          }}
                        >
                          YES
                        </span>
                      ) : (
                        <span style={{ color: "#B0A999" }}>—</span>
                      )}
                    </td>

                    {/* Confidence */}
                    <td>
                      <span
                        style={{
                          fontFamily: "var(--font-jetbrains-mono)",
                          fontSize: 12,
                          color: "#0C1222",
                        }}
                      >
                        {Math.round(entry.confidence * 100)}%
                      </span>
                    </td>

                    {/* Notes */}
                    <td>
                      {entry.notes ? (
                        <span
                          title={entry.notes}
                          style={{
                            fontSize: 12,
                            color: "#7A7568",
                            maxWidth: 200,
                            display: "inline-block",
                            whiteSpace: "nowrap",
                            overflow: "hidden",
                            textOverflow: "ellipsis",
                            verticalAlign: "middle",
                          }}
                        >
                          {entry.notes}
                        </span>
                      ) : (
                        <span style={{ color: "#B0A999", fontSize: 12 }}>—</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
