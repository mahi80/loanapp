"use client";

import { useState } from "react";
import { DocRulesPanel } from "./doc-rules-panel";
import { RateCardsPanel } from "./rate-cards-panel";
import { ProductRulesPanel } from "./product-rules-panel";
import { AgentsPanel } from "./agents-panel";

type SubTab = "documents" | "rate-cards" | "product-rules" | "agents";

const SUB_TABS: { id: SubTab; label: string }[] = [
  { id: "documents", label: "Document Rules" },
  { id: "rate-cards", label: "Rate Cards" },
  { id: "product-rules", label: "Product Rules" },
  { id: "agents", label: "Agents" },
];

export function SettingsTab() {
  const [activeSubTab, setActiveSubTab] = useState<SubTab>("documents");

  return (
    <div>
      {/* Header row */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "flex-start",
          marginBottom: 20,
        }}
      >
        {/* Left: title + subtitle */}
        <div>
          <div
            style={{
              fontFamily: "var(--font-dm-serif)",
              fontSize: 24,
              color: "#0C1222",
              lineHeight: 1.1,
            }}
          >
            Settings
          </div>
          <div
            style={{
              fontSize: 13,
              color: "#B0A999",
              marginTop: 4,
            }}
          >
            Configure document rules, rates, and agent behavior
          </div>
        </div>

        {/* Right: sub-tab pills */}
        <div className="settings-tabs">
          {SUB_TABS.map((tab) => (
            <button
              key={tab.id}
              className={`settings-tab${activeSubTab === tab.id ? " active" : ""}`}
              onClick={() => setActiveSubTab(tab.id)}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Content area */}
      {activeSubTab === "documents" && <DocRulesPanel />}
      {activeSubTab === "rate-cards" && <RateCardsPanel />}
      {activeSubTab === "product-rules" && <ProductRulesPanel />}
      {activeSubTab === "agents" && <AgentsPanel />}
    </div>
  );
}
