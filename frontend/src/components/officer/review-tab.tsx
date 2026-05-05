"use client";

import { useState, useEffect, useCallback } from "react";
import { useSession } from "next-auth/react";
import { Eye, X, ChevronDown, ChevronUp } from "lucide-react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface QueueItem {
  application_id: string;
  applicant_name: string;
  reference_number: string;
  loan_amount: number;
  composite_score: number;
  risk_flags: string[];
  waiting_since: string;
  escalation_reason: string;
  priority: string;
  agent_recommendation: string;
}

interface DetailData {
  application_id: string;
  full_application_data: {
    applicant_name: string;
    loan_amount: number;
    loan_type: string;
    status: string;
  };
  agent_outputs: { agent: string; output: Record<string, unknown> }[];
  recommended_decision: string;
  risk_flags: string[];
}

function getInitials(name: string): string {
  return name
    .split(" ")
    .map((w) => w[0])
    .join("")
    .toUpperCase()
    .slice(0, 2);
}

function formatINR(amount: number): string {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(amount);
}

function formatWaiting(since: string): { label: string; urgent: boolean } {
  const diffMs = Date.now() - new Date(since).getTime();
  const totalMins = Math.floor(diffMs / 60000);
  const hours = Math.floor(totalMins / 60);
  const mins = totalMins % 60;
  return {
    label: `${hours}h ${mins}m`,
    urgent: hours >= 2,
  };
}

function AgentOutputAccordion({
  agent,
  output,
}: {
  agent: string;
  output: Record<string, unknown>;
}) {
  const [open, setOpen] = useState(false);

  return (
    <div
      style={{
        borderRadius: "10px",
        border: "1px solid rgba(12,18,34,0.06)",
        overflow: "hidden",
        marginBottom: "8px",
      }}
    >
      <button
        onClick={() => setOpen((v) => !v)}
        style={{
          width: "100%",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "10px 14px",
          background: "#F5F2EA",
          border: "none",
          cursor: "pointer",
          textAlign: "left",
        }}
      >
        <span
          style={{
            fontSize: "12px",
            fontWeight: 600,
            textTransform: "uppercase",
            letterSpacing: "0.8px",
            color: "#7A7568",
          }}
        >
          {agent.replace(/_/g, " ")}
        </span>
        {open ? (
          <ChevronUp size={14} color="#7A7568" />
        ) : (
          <ChevronDown size={14} color="#7A7568" />
        )}
      </button>
      {open && (
        <div style={{ background: "#FFFDF8", padding: "0 14px 12px" }}>
          <pre
            style={{
              fontSize: "12px",
              fontFamily: "var(--font-jetbrains-mono, monospace)",
              maxHeight: "128px",
              overflowY: "auto",
              background: "#F5F2EA",
              borderRadius: "8px",
              padding: "12px",
              margin: "10px 0 0",
              whiteSpace: "pre-wrap",
              wordBreak: "break-all",
              color: "#0C1222",
            }}
          >
            {JSON.stringify(output, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
}

export function ReviewTab() {
  const { data: session } = useSession();
  const [queue, setQueue] = useState<QueueItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [detail, setDetail] = useState<DetailData | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [notes, setNotes] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  const token = (session as any)?.backendToken as string;

  const fetchQueue = useCallback(() => {
    if (!session) return;
    setLoading(true);
    fetch(`${API_URL}/api/v1/hitl/queue`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((r) => r.json())
      .then((data) => setQueue(data.items || []))
      .catch(() => setQueue([]))
      .finally(() => setLoading(false));
  }, [session, token]);

  useEffect(() => {
    fetchQueue();
  }, [fetchQueue]);

  useEffect(() => {
    if (!selectedId || !session) return;
    setDetailLoading(true);
    setDetail(null);
    setNotes("");
    fetch(`${API_URL}/api/v1/hitl/${selectedId}`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((r) => r.json())
      .then((data) => setDetail(data))
      .catch(() => setDetail(null))
      .finally(() => setDetailLoading(false));
  }, [selectedId, session, token]);

  const handleReview = async (decision: "approved" | "denied" | "conditional") => {
    if (!selectedId) return;
    setSubmitting(true);
    try {
      const res = await fetch(`${API_URL}/api/v1/hitl/${selectedId}/review`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          decision,
          officer_notes: notes,
          override_reason: notes,
        }),
      });
      if (res.ok) {
        setSuccessMsg(`Decision "${decision}" submitted successfully.`);
        setTimeout(() => {
          setSuccessMsg(null);
          setSelectedId(null);
          setDetail(null);
          fetchQueue();
        }, 1800);
      }
    } catch {
      // silently fail — officer can retry
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div style={{ animation: "fadeUp 0.45s cubic-bezier(0.16,1,0.3,1) both" }}>
      {/* Header */}
      <div style={{ marginBottom: "20px" }}>
        <h2
          style={{
            fontFamily: "var(--font-dm-serif, serif)",
            fontSize: "24px",
            fontWeight: 400,
            color: "#0C1222",
            margin: 0,
          }}
        >
          Review Queue
        </h2>
        <p
          style={{
            fontSize: "13px",
            color: "#B0A999",
            margin: "4px 0 0",
          }}
        >
          Applications escalated by AI for human decision
        </p>
      </div>

      {/* Queue Table */}
      <div className="officer-card" style={{ marginBottom: selectedId ? "20px" : 0 }}>
        {loading ? (
          <div
            style={{
              padding: "48px 24px",
              textAlign: "center",
              color: "#B0A999",
              fontSize: "13px",
            }}
          >
            Loading queue…
          </div>
        ) : queue.length === 0 ? (
          <div
            style={{
              padding: "56px 24px",
              textAlign: "center",
              color: "#B0A999",
              fontSize: "14px",
            }}
          >
            No applications pending review.
          </div>
        ) : (
          <div style={{ overflowX: "auto" }}>
            <table className="officer-table">
              <thead>
                <tr>
                  <th>Applicant</th>
                  <th>Reference</th>
                  <th>Amount</th>
                  <th>AI Score</th>
                  <th>Risk Flags</th>
                  <th>Waiting</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {queue.map((item) => {
                  const waiting = formatWaiting(item.waiting_since);
                  const isSelected = selectedId === item.application_id;
                  return (
                    <tr
                      key={item.application_id}
                      style={
                        isSelected
                          ? { background: "#F5F2EA" }
                          : undefined
                      }
                    >
                      {/* Applicant */}
                      <td>
                        <div
                          style={{
                            display: "flex",
                            alignItems: "center",
                            gap: "10px",
                          }}
                        >
                          <div
                            style={{
                              width: "34px",
                              height: "34px",
                              borderRadius: "12px",
                              background: "#FDF3E2",
                              color: "#8B5E00",
                              display: "flex",
                              alignItems: "center",
                              justifyContent: "center",
                              fontSize: "12px",
                              fontWeight: 700,
                              flexShrink: 0,
                            }}
                          >
                            {getInitials(item.applicant_name)}
                          </div>
                          <span style={{ fontWeight: 600, color: "#0C1222" }}>
                            {item.applicant_name}
                          </span>
                        </div>
                      </td>

                      {/* Reference */}
                      <td>
                        <span
                          style={{
                            fontFamily:
                              "var(--font-jetbrains-mono, monospace)",
                            fontSize: "12px",
                            color: "#7A7568",
                          }}
                        >
                          {item.reference_number}
                        </span>
                      </td>

                      {/* Amount */}
                      <td>
                        <span
                          style={{
                            fontFamily: "var(--font-dm-serif, serif)",
                            color: "#0C1222",
                          }}
                        >
                          {formatINR(item.loan_amount)}
                        </span>
                      </td>

                      {/* AI Score */}
                      <td>
                        <span
                          style={{
                            fontFamily:
                              "var(--font-jetbrains-mono, monospace)",
                            fontWeight: 600,
                            color: "#0C1222",
                          }}
                        >
                          {item.composite_score}
                        </span>
                      </td>

                      {/* Risk Flags */}
                      <td>
                        <div
                          style={{
                            display: "flex",
                            flexWrap: "wrap",
                            gap: "4px",
                          }}
                        >
                          {item.risk_flags.map((flag) => (
                            <span
                              key={flag}
                              className="status-badge badge-escalated"
                            >
                              {flag}
                            </span>
                          ))}
                        </div>
                      </td>

                      {/* Waiting */}
                      <td>
                        <span
                          style={{
                            fontFamily:
                              "var(--font-jetbrains-mono, monospace)",
                            fontSize: "12px",
                            fontWeight: waiting.urgent ? 600 : 400,
                            color: waiting.urgent ? "#D4860B" : "#7A7568",
                          }}
                        >
                          {waiting.label}
                        </span>
                      </td>

                      {/* Action */}
                      <td>
                        <button
                          onClick={() =>
                            setSelectedId(
                              isSelected ? null : item.application_id
                            )
                          }
                          style={{
                            display: "inline-flex",
                            alignItems: "center",
                            gap: "6px",
                            background: isSelected ? "#F5F2EA" : "#0C1222",
                            color: isSelected ? "#0C1222" : "#fff",
                            border: isSelected
                              ? "1px solid rgba(12,18,34,0.12)"
                              : "none",
                            borderRadius: "10px",
                            padding: "7px 14px",
                            fontSize: "13px",
                            fontWeight: 600,
                            cursor: "pointer",
                            transition: "all 0.2s",
                          }}
                        >
                          <Eye size={14} />
                          {isSelected ? "Close" : "Review"}
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Inline Detail Panel */}
      {selectedId && (
        <div
          className="officer-card"
          style={{
            padding: "24px",
            animation: "fadeUp 0.35s cubic-bezier(0.16,1,0.3,1) both",
          }}
        >
          {/* Panel Header */}
          <div
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              marginBottom: "20px",
            }}
          >
            <h3
              style={{
                fontFamily: "var(--font-dm-serif, serif)",
                fontSize: "18px",
                fontWeight: 400,
                color: "#0C1222",
                margin: 0,
              }}
            >
              Application Detail
            </h3>
            <button
              onClick={() => {
                setSelectedId(null);
                setDetail(null);
              }}
              style={{
                background: "none",
                border: "none",
                cursor: "pointer",
                color: "#7A7568",
                display: "flex",
                alignItems: "center",
                padding: "4px",
                borderRadius: "6px",
              }}
            >
              <X size={18} />
            </button>
          </div>

          {detailLoading && (
            <div
              style={{
                padding: "40px",
                textAlign: "center",
                color: "#B0A999",
                fontSize: "13px",
              }}
            >
              Loading details…
            </div>
          )}

          {successMsg && (
            <div
              style={{
                padding: "16px 20px",
                background: "#E8F5EE",
                color: "#1B6B3A",
                borderRadius: "10px",
                fontSize: "14px",
                fontWeight: 600,
                marginBottom: "16px",
                textAlign: "center",
              }}
            >
              {successMsg}
            </div>
          )}

          {detail && !detailLoading && (
            <>
              {/* 2-column grid */}
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "1fr 1fr",
                  gap: "24px",
                  marginBottom: "20px",
                }}
              >
                {/* Left: Application Info */}
                <div
                  style={{
                    background: "#F5F2EA",
                    borderRadius: "12px",
                    padding: "20px",
                  }}
                >
                  <p
                    style={{
                      fontSize: "10px",
                      fontWeight: 600,
                      textTransform: "uppercase",
                      letterSpacing: "1px",
                      color: "#B0A999",
                      margin: "0 0 14px",
                    }}
                  >
                    Application Info
                  </p>
                  {[
                    {
                      label: "Applicant Name",
                      value: detail.full_application_data.applicant_name,
                    },
                    {
                      label: "Amount",
                      value: formatINR(detail.full_application_data.loan_amount),
                    },
                    {
                      label: "Loan Type",
                      value: detail.full_application_data.loan_type
                        .replace(/_/g, " ")
                        .replace(/\b\w/g, (c) => c.toUpperCase()),
                    },
                    {
                      label: "Status",
                      value: detail.full_application_data.status
                        .replace(/_/g, " ")
                        .replace(/\b\w/g, (c) => c.toUpperCase()),
                    },
                  ].map(({ label, value }) => (
                    <div key={label} style={{ marginBottom: "12px" }}>
                      <div
                        style={{
                          fontSize: "11px",
                          color: "#B0A999",
                          marginBottom: "2px",
                        }}
                      >
                        {label}
                      </div>
                      <div
                        style={{
                          fontSize: "14px",
                          fontWeight: 600,
                          color: "#0C1222",
                        }}
                      >
                        {value}
                      </div>
                    </div>
                  ))}
                </div>

                {/* Right: AI Recommendation */}
                <div
                  style={{
                    background: "#F5F2EA",
                    borderRadius: "12px",
                    padding: "20px",
                  }}
                >
                  <p
                    style={{
                      fontSize: "10px",
                      fontWeight: 600,
                      textTransform: "uppercase",
                      letterSpacing: "1px",
                      color: "#B0A999",
                      margin: "0 0 14px",
                    }}
                  >
                    AI Recommendation
                  </p>
                  <div style={{ marginBottom: "16px" }}>
                    <div
                      style={{
                        fontSize: "11px",
                        color: "#B0A999",
                        marginBottom: "6px",
                      }}
                    >
                      Decision
                    </div>
                    <span className="status-badge badge-escalated">
                      {detail.recommended_decision.replace(/_/g, " ")}
                    </span>
                  </div>
                  <div>
                    <div
                      style={{
                        fontSize: "11px",
                        color: "#B0A999",
                        marginBottom: "8px",
                      }}
                    >
                      Risk Flags
                    </div>
                    <div
                      style={{
                        display: "flex",
                        flexWrap: "wrap",
                        gap: "6px",
                      }}
                    >
                      {detail.risk_flags.map((flag) => (
                        <span
                          key={flag}
                          className="status-badge badge-escalated"
                        >
                          {flag}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              </div>

              {/* Agent Outputs Accordion */}
              <div style={{ marginBottom: "20px" }}>
                <p
                  style={{
                    fontSize: "11px",
                    fontWeight: 600,
                    textTransform: "uppercase",
                    letterSpacing: "1px",
                    color: "#B0A999",
                    margin: "0 0 10px",
                  }}
                >
                  Agent Outputs
                </p>
                {detail.agent_outputs.length === 0 ? (
                  <p style={{ fontSize: "13px", color: "#B0A999" }}>
                    No agent outputs available.
                  </p>
                ) : (
                  detail.agent_outputs.map((ao, i) => (
                    <AgentOutputAccordion
                      key={`${ao.agent}-${i}`}
                      agent={ao.agent}
                      output={ao.output}
                    />
                  ))
                )}
              </div>

              {/* Action Bar */}
              <div
                style={{
                  borderTop: "1px solid rgba(12,18,34,0.06)",
                  paddingTop: "20px",
                }}
              >
                <textarea
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  placeholder="Add notes (optional)..."
                  disabled={submitting}
                  style={{
                    width: "100%",
                    minHeight: "60px",
                    borderRadius: "10px",
                    border: "1px solid rgba(12,18,34,0.12)",
                    padding: "12px",
                    fontSize: "13px",
                    fontFamily: "var(--font-dm-sans, sans-serif)",
                    color: "#0C1222",
                    background: "#FFFDF8",
                    resize: "vertical",
                    boxSizing: "border-box",
                    marginBottom: "14px",
                    outline: "none",
                  }}
                />
                <div style={{ display: "flex", gap: "12px", flexWrap: "wrap" }}>
                  <button
                    onClick={() => handleReview("approved")}
                    disabled={submitting}
                    style={{
                      background: "#2E8B57",
                      color: "#fff",
                      border: "none",
                      borderRadius: "10px",
                      padding: "10px 24px",
                      fontSize: "13px",
                      fontWeight: 600,
                      cursor: submitting ? "not-allowed" : "pointer",
                      opacity: submitting ? 0.6 : 1,
                      transition: "opacity 0.2s",
                    }}
                  >
                    Approve
                  </button>
                  <button
                    onClick={() => handleReview("conditional")}
                    disabled={submitting}
                    style={{
                      background: "#3B7DDD",
                      color: "#fff",
                      border: "none",
                      borderRadius: "10px",
                      padding: "10px 24px",
                      fontSize: "13px",
                      fontWeight: 600,
                      cursor: submitting ? "not-allowed" : "pointer",
                      opacity: submitting ? 0.6 : 1,
                      transition: "opacity 0.2s",
                    }}
                  >
                    Conditional
                  </button>
                  <button
                    onClick={() => handleReview("denied")}
                    disabled={submitting}
                    style={{
                      background: "#C0392B",
                      color: "#fff",
                      border: "none",
                      borderRadius: "10px",
                      padding: "10px 24px",
                      fontSize: "13px",
                      fontWeight: 600,
                      cursor: submitting ? "not-allowed" : "pointer",
                      opacity: submitting ? 0.6 : 1,
                      transition: "opacity 0.2s",
                    }}
                  >
                    Deny
                  </button>
                </div>
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
}
