"use client";

import { useState, useEffect, useCallback } from "react";
import { useSession } from "next-auth/react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface RateCard {
  id: string;
  product_type: string;
  risk_category: string;
  interest_rate: number;
  processing_fee_pct: number;
  insurance_pct?: number;
}

interface EditState {
  interest_rate: string;
  processing_fee_pct: string;
  insurance_pct: string;
}

const SCORE_RANGES: Record<string, string> = {
  low: "700 – 900",
  medium: "600 – 699",
  high: "450 – 599",
  very_high: "300 – 449",
};

const RISK_ORDER = ["low", "medium", "high", "very_high"];

const RISK_LABELS: Record<string, string> = {
  low: "Low",
  medium: "Medium",
  high: "High",
  very_high: "Very High",
};

function inputStyle(override?: React.CSSProperties): React.CSSProperties {
  return {
    width: 60,
    textAlign: "center",
    border: "1px solid rgba(12,18,34,0.15)",
    borderRadius: 6,
    padding: "4px 6px",
    fontFamily: "var(--font-jetbrains-mono)",
    fontSize: 13,
    background: "#FFFDF8",
    color: "#0C1222",
    outline: "none",
    ...override,
  };
}

function RateCardRow({
  card,
  onSaved,
  token,
}: {
  card: RateCard;
  onSaved: (updated: RateCard) => void;
  token: string;
}) {
  const isDenied = card.risk_category === "very_high";
  const [editing, setEditing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [editState, setEditState] = useState<EditState>({
    interest_rate: String(card.interest_rate ?? ""),
    processing_fee_pct: String(card.processing_fee_pct ?? ""),
    insurance_pct: String(card.insurance_pct ?? ""),
  });

  function startEdit() {
    setEditState({
      interest_rate: String(card.interest_rate ?? ""),
      processing_fee_pct: String(card.processing_fee_pct ?? ""),
      insurance_pct: String(card.insurance_pct ?? ""),
    });
    setEditing(true);
  }

  function cancelEdit() {
    setEditing(false);
  }

  async function saveEdit() {
    setSaving(true);
    try {
      const body: Record<string, number> = {
        interest_rate: parseFloat(editState.interest_rate) || 0,
        processing_fee_pct: parseFloat(editState.processing_fee_pct) || 0,
        insurance_pct: parseFloat(editState.insurance_pct) || 0,
      };
      const res = await fetch(`${API_URL}/api/v1/config/rate-cards/${card.id}`, {
        method: "PUT",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify(body),
      });
      if (!res.ok) throw new Error("Save failed");
      const updated: RateCard = await res.json();
      onSaved(updated);
      setEditing(false);
    } catch {
      // keep editing open so user can retry
    } finally {
      setSaving(false);
    }
  }

  const monoCell: React.CSSProperties = {
    fontFamily: "var(--font-jetbrains-mono)",
    fontSize: 13,
  };

  return (
    <tr>
      {/* Risk Category */}
      <td>
        <span
          style={{
            fontWeight: 600,
            fontSize: 13,
            color:
              card.risk_category === "low"
                ? "#2E8B57"
                : card.risk_category === "medium"
                ? "#D4860B"
                : card.risk_category === "high"
                ? "#C0392B"
                : "#922020",
          }}
        >
          {RISK_LABELS[card.risk_category] ?? card.risk_category}
        </span>
      </td>

      {/* Score Range */}
      <td style={monoCell}>{SCORE_RANGES[card.risk_category] ?? "—"}</td>

      {/* Interest Rate */}
      <td style={monoCell}>
        {isDenied ? (
          <span style={{ color: "#922020", fontWeight: 700 }}>Denied</span>
        ) : editing ? (
          <input
            type="number"
            style={inputStyle()}
            value={editState.interest_rate}
            onChange={(e) =>
              setEditState((s) => ({ ...s, interest_rate: e.target.value }))
            }
          />
        ) : (
          `${card.interest_rate}%`
        )}
      </td>

      {/* Processing Fee */}
      <td style={monoCell}>
        {isDenied ? (
          <span style={{ color: "#B0A999" }}>—</span>
        ) : editing ? (
          <input
            type="number"
            style={inputStyle()}
            value={editState.processing_fee_pct}
            onChange={(e) =>
              setEditState((s) => ({ ...s, processing_fee_pct: e.target.value }))
            }
          />
        ) : (
          `${card.processing_fee_pct}%`
        )}
      </td>

      {/* Insurance */}
      <td style={monoCell}>
        {isDenied ? (
          <span style={{ color: "#B0A999" }}>—</span>
        ) : editing ? (
          <input
            type="number"
            style={inputStyle()}
            value={editState.insurance_pct}
            onChange={(e) =>
              setEditState((s) => ({ ...s, insurance_pct: e.target.value }))
            }
          />
        ) : card.insurance_pct != null ? (
          `${card.insurance_pct}%`
        ) : (
          "—"
        )}
      </td>

      {/* Action */}
      <td>
        {isDenied ? null : editing ? (
          <div style={{ display: "flex", gap: 6, alignItems: "center" }}>
            <button
              onClick={saveEdit}
              disabled={saving}
              style={{
                background: "#C8A24E",
                color: "#0C1222",
                border: "none",
                borderRadius: 8,
                padding: "5px 14px",
                fontSize: 12,
                fontWeight: 700,
                cursor: saving ? "not-allowed" : "pointer",
                opacity: saving ? 0.7 : 1,
              }}
            >
              {saving ? "…" : "Save"}
            </button>
            <button
              onClick={cancelEdit}
              style={{
                background: "transparent",
                color: "#7A7568",
                border: "1px solid rgba(12,18,34,0.12)",
                borderRadius: 8,
                padding: "5px 12px",
                fontSize: 12,
                fontWeight: 500,
                cursor: "pointer",
              }}
            >
              Cancel
            </button>
          </div>
        ) : (
          <button
            onClick={startEdit}
            style={{
              background: "transparent",
              color: "#7A7568",
              border: "1px solid rgba(12,18,34,0.12)",
              borderRadius: 8,
              padding: "5px 14px",
              fontSize: 12,
              fontWeight: 500,
              cursor: "pointer",
            }}
          >
            Edit
          </button>
        )}
      </td>
    </tr>
  );
}

export function RateCardsPanel() {
  const { data: session } = useSession();
  const [cards, setCards] = useState<RateCard[]>([]);
  const [loading, setLoading] = useState(true);

  const token = (session as any)?.backendToken as string ?? "";

  const fetchCards = useCallback(async () => {
    if (!token) return;
    setLoading(true);
    try {
      const res = await fetch(`${API_URL}/api/v1/config/rate-cards`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error("Failed");
      const data = await res.json();
      setCards(Array.isArray(data) ? data : []);
    } catch {
      setCards([]);
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    fetchCards();
  }, [fetchCards]);

  function handleSaved(updated: RateCard) {
    setCards((prev) => prev.map((c) => (c.id === updated.id ? updated : c)));
  }

  // Group by product_type
  const grouped = cards.reduce<Record<string, RateCard[]>>((acc, card) => {
    const key = card.product_type;
    if (!acc[key]) acc[key] = [];
    acc[key].push(card);
    return acc;
  }, {});

  const productTypes = Object.keys(grouped);

  // Sort rows within each group by risk order
  for (const pt of productTypes) {
    grouped[pt].sort(
      (a, b) =>
        RISK_ORDER.indexOf(a.risk_category) - RISK_ORDER.indexOf(b.risk_category)
    );
  }

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

  if (cards.length === 0) {
    return (
      <div
        style={{
          textAlign: "center",
          padding: "60px 0",
          color: "#B0A999",
          fontSize: 13,
        }}
      >
        No rate card configuration found.
      </div>
    );
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
      {productTypes.map((pt) => (
        <div key={pt} className="officer-card" style={{ overflow: "visible" }}>
          {/* Product type sub-header (only if more than one type) */}
          {productTypes.length > 1 && (
            <div
              style={{
                padding: "18px 20px 0",
                fontFamily: "var(--font-dm-serif)",
                fontSize: 17,
                color: "#0C1222",
              }}
            >
              {pt.charAt(0).toUpperCase() + pt.slice(1)} Loan
            </div>
          )}

          <div style={{ overflowX: "auto" }}>
            <table className="officer-table">
              <thead>
                <tr>
                  <th>Risk Category</th>
                  <th>Score Range</th>
                  <th>Interest Rate (%)</th>
                  <th>Processing Fee (%)</th>
                  <th>Insurance (%)</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {grouped[pt].map((card) => (
                  <RateCardRow
                    key={card.id}
                    card={card}
                    token={token}
                    onSaved={handleSaved}
                  />
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ))}
    </div>
  );
}
