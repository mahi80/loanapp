"use client";

import { useState, useEffect, useCallback } from "react";
import { useSession } from "next-auth/react";
import { User, Briefcase, Store, Info } from "lucide-react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

type LoanType = "personal" | "home" | "auto" | "business";
type Tier = "mandatory" | "recommended" | "optional";

interface DocItem {
  name: string;
  key: string;
  description: string;
  tier: Tier;
  enabled: boolean;
}

interface DocGroup {
  group: string;
  label: string;
  icon: string;
  description: string;
  documents: DocItem[];
}

interface DocConfig {
  groups: DocGroup[];
}

const LOAN_TABS: { id: LoanType; label: string }[] = [
  { id: "personal", label: "Personal Loan" },
  { id: "home", label: "Home Loan" },
  { id: "auto", label: "Auto Loan" },
  { id: "business", label: "Business" },
];

function getGroupIcon(iconKey: string, group: string) {
  if (group === "salaried") return <Briefcase size={18} color="#C8A24E" />;
  if (group === "self_employed") return <Store size={18} color="#C8A24E" />;
  return <User size={18} color="#C8A24E" />;
}

function TierBadge({ tier }: { tier: Tier }) {
  const labelMap: Record<Tier, string> = {
    mandatory: "MANDATORY",
    recommended: "RECOMMENDED",
    optional: "OPTIONAL",
  };
  return (
    <span
      className={`tier-${tier}`}
      style={{
        padding: "3px 10px",
        borderRadius: 6,
        fontSize: 10,
        fontWeight: 700,
        letterSpacing: "0.5px",
        textTransform: "uppercase",
      }}
    >
      {labelMap[tier]}
    </span>
  );
}

export function DocRulesPanel() {
  const { data: session } = useSession();
  const [selectedLoanType, setSelectedLoanType] = useState<LoanType>("personal");
  const [groups, setGroups] = useState<DocGroup[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saveStatus, setSaveStatus] = useState<"idle" | "saved" | "error">("idle");

  const fetchConfig = useCallback(async () => {
    if (!session) return;
    const token = (session as any)?.backendToken as string;
    setLoading(true);
    try {
      const res = await fetch(
        `${API_URL}/api/v1/config/document-requirements?loan_type=${selectedLoanType}`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      if (!res.ok) throw new Error("Failed to fetch");
      const data = await res.json();

      // API returns the config directly (groups at top level), but handle both cases
      let cfg: DocConfig;
      if (data && Array.isArray(data.groups)) {
        cfg = data as DocConfig;
      } else if (data && data.config && Array.isArray(data.config.groups)) {
        cfg = data.config as DocConfig;
      } else {
        cfg = { groups: [] };
      }
      setGroups(cfg.groups);
    } catch {
      setGroups([]);
    } finally {
      setLoading(false);
    }
  }, [session, selectedLoanType]);

  useEffect(() => {
    fetchConfig();
  }, [fetchConfig]);

  function toggleDoc(groupIndex: number, docIndex: number) {
    setGroups((prev) =>
      prev.map((g, gi) =>
        gi !== groupIndex
          ? g
          : {
              ...g,
              documents: g.documents.map((d, di) =>
                di !== docIndex ? d : { ...d, enabled: !d.enabled }
              ),
            }
      )
    );
  }

  async function handleSave() {
    if (!session) return;
    const token = (session as any)?.backendToken as string;
    setSaving(true);
    setSaveStatus("idle");
    try {
      const res = await fetch(`${API_URL}/api/v1/config/document-requirements`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          loan_type: selectedLoanType,
          config: { groups },
        }),
      });
      if (!res.ok) throw new Error("Save failed");
      setSaveStatus("saved");
      // Refetch to confirm
      await fetchConfig();
      setTimeout(() => setSaveStatus("idle"), 2000);
    } catch {
      setSaveStatus("error");
      setTimeout(() => setSaveStatus("idle"), 2000);
    } finally {
      setSaving(false);
    }
  }

  const saveButtonStyle: React.CSSProperties = {
    background:
      saveStatus === "saved"
        ? "#2E8B57"
        : saveStatus === "error"
        ? "#C0392B"
        : "#C8A24E",
    color: saveStatus === "saved" || saveStatus === "error" ? "#fff" : "#0C1222",
    border: "none",
    borderRadius: 10,
    padding: "12px 32px",
    fontSize: 13,
    fontWeight: 700,
    letterSpacing: "0.3px",
    cursor: saving ? "not-allowed" : "pointer",
    transition: "all 0.2s",
    opacity: saving ? 0.7 : 1,
  };

  return (
    <div>
      {/* Level 2: Loan type tabs */}
      <div style={{ marginBottom: 20 }}>
        <div className="settings-tabs">
          {LOAN_TABS.map((tab) => (
            <button
              key={tab.id}
              className={`settings-tab${selectedLoanType === tab.id ? " active" : ""}`}
              style={{ fontSize: 12 }}
              onClick={() => setSelectedLoanType(tab.id)}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* 3-column grid */}
      {loading ? (
        <div
          style={{
            textAlign: "center",
            padding: "60px 0",
            color: "#B0A999",
            fontSize: 13,
          }}
        >
          Loading…
        </div>
      ) : groups.length === 0 ? (
        <div
          style={{
            textAlign: "center",
            padding: "60px 0",
            color: "#B0A999",
            fontSize: 13,
          }}
        >
          No document configuration found for this loan type.
        </div>
      ) : (
        <div className="officer-grid" style={{ marginBottom: 16 }}>
          {groups.map((group, gi) => (
            <div
              key={group.group}
              className="officer-card"
              style={{
                gridColumn: "span 4",
                padding: "24px 28px",
              }}
            >
              {/* Card header */}
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 8,
                  marginBottom: 4,
                }}
              >
                {getGroupIcon(group.icon, group.group)}
                <span
                  style={{
                    fontFamily: "var(--font-dm-serif)",
                    fontSize: 16,
                    color: "#0C1222",
                    lineHeight: 1.2,
                  }}
                >
                  {group.label}
                </span>
              </div>

              {/* Subtitle */}
              <p
                style={{
                  fontSize: 11,
                  color: "#B0A999",
                  marginBottom: 16,
                  marginTop: 0,
                }}
              >
                {group.description}
              </p>

              {/* Document rows */}
              <div>
                {group.documents.map((doc, di) => {
                  const isLast = di === group.documents.length - 1;
                  return (
                    <div
                      key={doc.key}
                      style={{
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "space-between",
                        paddingTop: 12,
                        paddingBottom: 12,
                        borderBottom: isLast
                          ? "none"
                          : "1px solid rgba(12,18,34,0.06)",
                      }}
                    >
                      {/* Left: name + description */}
                      <div style={{ flex: 1, minWidth: 0, paddingRight: 12 }}>
                        <div
                          style={{
                            fontSize: 13,
                            fontWeight: 600,
                            color: "#0C1222",
                          }}
                        >
                          {doc.name}
                        </div>
                        <div
                          style={{
                            fontSize: 11,
                            color: "#B0A999",
                            marginTop: 1,
                          }}
                        >
                          {doc.description}
                        </div>
                      </div>

                      {/* Right: tier badge + toggle */}
                      <div
                        style={{
                          display: "flex",
                          alignItems: "center",
                          gap: 10,
                          flexShrink: 0,
                        }}
                      >
                        <TierBadge tier={doc.tier} />
                        <div
                          className={`toggle-switch ${doc.enabled ? "on" : "off"}`}
                          onClick={() => toggleDoc(gi, di)}
                          role="switch"
                          aria-checked={doc.enabled}
                          aria-label={`Toggle ${doc.name}`}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Footer bar — full width */}
      <div
        style={{
          background: "#0C1222",
          borderRadius: 16,
          padding: "18px 28px",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginTop: 4,
        }}
      >
        {/* Left: info text */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 8,
            fontSize: 13,
            color: "#8A8E96",
          }}
        >
          <Info size={16} color="#8A8E96" />
          Changes apply to the AI agent immediately for new conversations.
        </div>

        {/* Right: Save button */}
        <button
          style={saveButtonStyle}
          onClick={handleSave}
          disabled={saving}
          onMouseEnter={(e) => {
            if (!saving && saveStatus === "idle") {
              (e.currentTarget as HTMLButtonElement).style.background = "#E8D5A0";
              (e.currentTarget as HTMLButtonElement).style.transform = "translateY(-1px)";
              (e.currentTarget as HTMLButtonElement).style.boxShadow =
                "0 4px 12px rgba(200,162,78,0.3)";
            }
          }}
          onMouseLeave={(e) => {
            if (!saving && saveStatus === "idle") {
              (e.currentTarget as HTMLButtonElement).style.background = "#C8A24E";
              (e.currentTarget as HTMLButtonElement).style.transform = "translateY(0)";
              (e.currentTarget as HTMLButtonElement).style.boxShadow = "none";
            }
          }}
        >
          {saveStatus === "saved"
            ? "Saved!"
            : saveStatus === "error"
            ? "Error — Retry"
            : saving
            ? "Saving…"
            : "Save & Update Agent"}
        </button>
      </div>
    </div>
  );
}
