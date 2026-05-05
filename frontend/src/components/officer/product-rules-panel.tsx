"use client";

import { useState, useEffect, useCallback } from "react";
import { useSession } from "next-auth/react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface ProductRule {
  id: string;
  product_type: string;
  rule_name: string;
  rule_type: string;
  rule_config: Record<string, number>;
}

// draft edits per rule id
type Drafts = Record<string, Record<string, string>>;

const PRODUCT_ORDER = ["personal", "home", "auto", "business"];

const PRODUCT_LABELS: Record<string, string> = {
  personal: "Personal Loan",
  home: "Home Loan",
  auto: "Auto Loan",
  business: "Business Loan",
};

function labelForRule(rule_name: string): string {
  if (rule_name === "min_age") return "Age Range";
  if (rule_name === "min_income") return "Min Monthly Income";
  if (rule_name === "max_multiplier") return "Max Loan-to-Income";
  return rule_name;
}

function numInputStyle(): React.CSSProperties {
  return {
    width: 96,
    fontFamily: "var(--font-jetbrains-mono)",
    fontSize: 13,
    border: "1px solid rgba(12,18,34,0.15)",
    borderRadius: 6,
    padding: "6px 12px",
    background: "#FFFDF8",
    color: "#0C1222",
    outline: "none",
  };
}

function labelStyle(): React.CSSProperties {
  return {
    fontSize: 13,
    fontWeight: 600,
    color: "#0C1222",
    minWidth: 160,
  };
}

function RuleRow({
  rule,
  draft,
  onDraftChange,
}: {
  rule: ProductRule;
  draft: Record<string, string>;
  onDraftChange: (field: string, value: string) => void;
}) {
  if (rule.rule_name === "min_age") {
    const minAge = draft["min_age"] ?? String(rule.rule_config["min_age"] ?? "");
    const maxAge = draft["max_age"] ?? String(rule.rule_config["max_age"] ?? "");
    return (
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 12,
          paddingTop: 12,
          paddingBottom: 12,
          borderBottom: "1px solid rgba(12,18,34,0.06)",
        }}
      >
        <span style={labelStyle()}>Age Range</span>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <input
            type="number"
            style={numInputStyle()}
            value={minAge}
            placeholder="Min"
            onChange={(e) => onDraftChange("min_age", e.target.value)}
          />
          <span style={{ color: "#B0A999", fontSize: 12 }}>to</span>
          <input
            type="number"
            style={numInputStyle()}
            value={maxAge}
            placeholder="Max"
            onChange={(e) => onDraftChange("max_age", e.target.value)}
          />
          <span style={{ color: "#B0A999", fontSize: 12 }}>years</span>
        </div>
      </div>
    );
  }

  if (rule.rule_name === "min_income") {
    const val =
      draft["min_monthly_income"] ??
      String(rule.rule_config["min_monthly_income"] ?? "");
    return (
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 12,
          paddingTop: 12,
          paddingBottom: 12,
          borderBottom: "1px solid rgba(12,18,34,0.06)",
        }}
      >
        <span style={labelStyle()}>Min Monthly Income</span>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <span style={{ color: "#7A7568", fontSize: 13 }}>₹</span>
          <input
            type="number"
            style={numInputStyle()}
            value={val}
            placeholder="Amount"
            onChange={(e) => onDraftChange("min_monthly_income", e.target.value)}
          />
        </div>
      </div>
    );
  }

  if (rule.rule_name === "max_multiplier") {
    const val =
      draft["max_multiplier"] ?? String(rule.rule_config["max_multiplier"] ?? "");
    return (
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 12,
          paddingTop: 12,
          paddingBottom: 12,
          borderBottom: "1px solid rgba(12,18,34,0.06)",
        }}
      >
        <span style={labelStyle()}>Max Loan-to-Income</span>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <input
            type="number"
            style={numInputStyle()}
            value={val}
            placeholder="Multiplier"
            onChange={(e) => onDraftChange("max_multiplier", e.target.value)}
          />
          <span style={{ color: "#7A7568", fontSize: 13 }}>x</span>
        </div>
      </div>
    );
  }

  // Generic fallback
  const firstKey = Object.keys(rule.rule_config)[0];
  const val = draft[firstKey] ?? String(rule.rule_config[firstKey] ?? "");
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: 12,
        paddingTop: 12,
        paddingBottom: 12,
        borderBottom: "1px solid rgba(12,18,34,0.06)",
      }}
    >
      <span style={labelStyle()}>{labelForRule(rule.rule_name)}</span>
      <input
        type="number"
        style={numInputStyle()}
        value={val}
        onChange={(e) => onDraftChange(firstKey, e.target.value)}
      />
    </div>
  );
}

function ProductCard({
  productType,
  rules,
  token,
}: {
  productType: string;
  rules: ProductRule[];
  token: string;
}) {
  const [drafts, setDrafts] = useState<Drafts>({});
  const [saving, setSaving] = useState(false);
  const [saveStatus, setSaveStatus] = useState<"idle" | "saved" | "error">("idle");

  function onDraftChange(ruleId: string, field: string, value: string) {
    setDrafts((prev) => ({
      ...prev,
      [ruleId]: { ...(prev[ruleId] ?? {}), [field]: value },
    }));
  }

  async function handleSave() {
    setSaving(true);
    setSaveStatus("idle");
    try {
      const promises = rules
        .filter((r) => drafts[r.id] && Object.keys(drafts[r.id]).length > 0)
        .map((r) => {
          const updatedConfig = { ...r.rule_config };
          for (const [k, v] of Object.entries(drafts[r.id])) {
            updatedConfig[k] = parseFloat(v) || 0;
          }
          return fetch(`${API_URL}/api/v1/config/product-rules/${r.id}`, {
            method: "PUT",
            headers: {
              Authorization: `Bearer ${token}`,
              "Content-Type": "application/json",
            },
            body: JSON.stringify({ rule_config: updatedConfig }),
          });
        });

      if (promises.length === 0) {
        setSaveStatus("saved");
        setTimeout(() => setSaveStatus("idle"), 2000);
        return;
      }

      const results = await Promise.all(promises);
      const anyFailed = results.some((r) => !r.ok);
      if (anyFailed) throw new Error("Some saves failed");
      setSaveStatus("saved");
      setDrafts({});
      setTimeout(() => setSaveStatus("idle"), 2000);
    } catch {
      setSaveStatus("error");
      setTimeout(() => setSaveStatus("idle"), 2000);
    } finally {
      setSaving(false);
    }
  }

  const label = PRODUCT_LABELS[productType] ?? productType;

  return (
    <div
      className="officer-card"
      style={{
        gridColumn: "span 6",
        padding: "24px 28px",
      }}
    >
      {/* Header */}
      <div
        style={{
          fontFamily: "var(--font-dm-serif)",
          fontSize: 17,
          color: "#0C1222",
          lineHeight: 1.2,
          marginBottom: 2,
        }}
      >
        {label}
      </div>
      <div
        style={{
          fontSize: 11,
          color: "#B0A999",
          marginBottom: 16,
        }}
      >
        Eligibility Rules
      </div>

      {/* Rules */}
      <div>
        {rules.map((rule) => (
          <RuleRow
            key={rule.id}
            rule={rule}
            draft={drafts[rule.id] ?? {}}
            onDraftChange={(field, value) => onDraftChange(rule.id, field, value)}
          />
        ))}
      </div>

      {/* Save button */}
      <div style={{ marginTop: 20 }}>
        <button
          onClick={handleSave}
          disabled={saving}
          style={{
            background:
              saveStatus === "saved"
                ? "#2E8B57"
                : saveStatus === "error"
                ? "#C0392B"
                : "#C8A24E",
            color:
              saveStatus === "saved" || saveStatus === "error" ? "#fff" : "#0C1222",
            border: "none",
            borderRadius: 10,
            padding: "10px 24px",
            fontSize: 13,
            fontWeight: 700,
            cursor: saving ? "not-allowed" : "pointer",
            opacity: saving ? 0.7 : 1,
            transition: "all 0.2s",
          }}
        >
          {saveStatus === "saved"
            ? "Saved!"
            : saveStatus === "error"
            ? "Error — Retry"
            : saving
            ? "Saving…"
            : "Save Changes"}
        </button>
      </div>
    </div>
  );
}

export function ProductRulesPanel() {
  const { data: session } = useSession();
  const [rules, setRules] = useState<ProductRule[]>([]);
  const [loading, setLoading] = useState(true);

  const token = (session as any)?.backendToken as string ?? "";

  const fetchRules = useCallback(async () => {
    if (!token) return;
    setLoading(true);
    try {
      const res = await fetch(`${API_URL}/api/v1/config/product-rules`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error("Failed");
      const data = await res.json();
      setRules(Array.isArray(data) ? data : []);
    } catch {
      setRules([]);
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    fetchRules();
  }, [fetchRules]);

  if (loading) {
    return (
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
    );
  }

  if (rules.length === 0) {
    return (
      <div
        style={{
          textAlign: "center",
          padding: "60px 0",
          color: "#B0A999",
          fontSize: 13,
        }}
      >
        No product rule configuration found.
      </div>
    );
  }

  // Group by product_type
  const grouped = rules.reduce<Record<string, ProductRule[]>>((acc, rule) => {
    const key = rule.product_type;
    if (!acc[key]) acc[key] = [];
    acc[key].push(rule);
    return acc;
  }, {});

  const productTypes = PRODUCT_ORDER.filter((pt) => grouped[pt]);

  return (
    <div className="officer-grid">
      {productTypes.map((pt) => (
        <ProductCard
          key={pt}
          productType={pt}
          rules={grouped[pt]}
          token={token}
        />
      ))}
    </div>
  );
}
