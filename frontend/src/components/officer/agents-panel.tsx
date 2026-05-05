"use client";

import { useState } from "react";
import {
  UserCheck,
  FileUp,
  ScanSearch,
  Database,
  IndianRupee,
  ShieldAlert,
  AlertTriangle,
  Calculator,
  ShieldCheck,
  Receipt,
  Scale,
  FileCheck,
  Users,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";

interface AgentDef {
  name: string;
  icon: string;
  description: string;
  latency: string;
  successRate: string;
  enabled: boolean;
}

const ICON_MAP: Record<string, LucideIcon> = {
  UserCheck,
  FileUp,
  ScanSearch,
  Database,
  IndianRupee,
  ShieldAlert,
  AlertTriangle,
  Calculator,
  ShieldCheck,
  Receipt,
  Scale,
  FileCheck,
  Users,
};

const AGENTS_STATIC: AgentDef[] = [
  {
    name: "Intake",
    icon: "UserCheck",
    description: "Collect applicant info and check eligibility",
    latency: "2.1s",
    successRate: "99.2%",
    enabled: true,
  },
  {
    name: "Document Collection",
    icon: "FileUp",
    description: "Request and receive required documents",
    latency: "1.8s",
    successRate: "98.7%",
    enabled: true,
  },
  {
    name: "Document Verification",
    icon: "ScanSearch",
    description: "OCR extraction and cross-validation",
    latency: "4.5s",
    successRate: "96.1%",
    enabled: true,
  },
  {
    name: "Bureau Pull",
    icon: "Database",
    description: "Fetch credit reports from CIBIL, Experian, CRIF, Equifax",
    latency: "3.2s",
    successRate: "97.8%",
    enabled: true,
  },
  {
    name: "Income Verification",
    icon: "IndianRupee",
    description: "Verify income from bank statements and payslips",
    latency: "2.8s",
    successRate: "98.3%",
    enabled: true,
  },
  {
    name: "Risk Assessment",
    icon: "ShieldAlert",
    description: "4Cs framework scoring and DTI calculation",
    latency: "3.7s",
    successRate: "99.5%",
    enabled: true,
  },
  {
    name: "Fraud Detection",
    icon: "AlertTriangle",
    description: "Identity, document, and pattern fraud checks",
    latency: "2.1s",
    successRate: "99.8%",
    enabled: true,
  },
  {
    name: "Score Aggregation",
    icon: "Calculator",
    description: "Combine scores into composite 300-900",
    latency: "0.5s",
    successRate: "100%",
    enabled: true,
  },
  {
    name: "Compliance",
    icon: "ShieldCheck",
    description: "RBI guidelines, fair lending, KYC validation",
    latency: "1.2s",
    successRate: "100%",
    enabled: true,
  },
  {
    name: "Pricing",
    icon: "Receipt",
    description: "Rate card lookup and EMI calculation",
    latency: "0.8s",
    successRate: "100%",
    enabled: true,
  },
  {
    name: "Decision",
    icon: "Scale",
    description: "Final credit decision with confidence scoring",
    latency: "2.3s",
    successRate: "92.7%",
    enabled: true,
  },
  {
    name: "Offer Generation",
    icon: "FileCheck",
    description: "Generate loan offer terms and EMI schedule",
    latency: "1.5s",
    successRate: "100%",
    enabled: true,
  },
  {
    name: "Human Review",
    icon: "Users",
    description: "Escalation to credit officer for borderline cases",
    latency: "—",
    successRate: "7.3% HITL",
    enabled: true,
  },
];

function successRateColor(rate: string): string {
  if (rate === "100%" || rate.startsWith("9")) return "#2E8B57";
  if (rate.startsWith("7")) return "#D4860B";
  return "#B0A999";
}

function AgentRow({
  agent,
  onToggle,
  isLast,
}: {
  agent: AgentDef & { _enabled: boolean };
  onToggle: () => void;
  isLast: boolean;
}) {
  const IconComp = ICON_MAP[agent.icon];

  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: 16,
        paddingTop: 12,
        paddingBottom: 12,
        borderBottom: isLast ? "none" : "1px solid rgba(12,18,34,0.06)",
        transition: "background 0.15s",
        borderRadius: isLast ? "0 0 16px 16px" : 0,
        paddingLeft: 20,
        paddingRight: 20,
        marginLeft: -20,
        marginRight: -20,
      }}
      onMouseEnter={(e) => {
        (e.currentTarget as HTMLDivElement).style.background = "#F5F2EA";
      }}
      onMouseLeave={(e) => {
        (e.currentTarget as HTMLDivElement).style.background = "transparent";
      }}
    >
      {/* Icon */}
      <div
        style={{
          width: 40,
          height: 40,
          borderRadius: 10,
          background: "#F5F2EA",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          flexShrink: 0,
        }}
      >
        {IconComp && <IconComp size={20} color="#7A7568" />}
      </div>

      {/* Name + Description */}
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ fontSize: 14, fontWeight: 600, color: "#0C1222" }}>
          {agent.name}
        </div>
        <div style={{ fontSize: 12, color: "#B0A999", marginTop: 1 }}>
          {agent.description}
        </div>
      </div>

      {/* Latency */}
      <div
        style={{
          fontFamily: "var(--font-jetbrains-mono)",
          fontSize: 13,
          fontWeight: 500,
          color: "#7A7568",
          width: 52,
          textAlign: "right",
          flexShrink: 0,
        }}
      >
        {agent.latency}
      </div>

      {/* Success Rate */}
      <div
        style={{
          fontFamily: "var(--font-jetbrains-mono)",
          fontSize: 13,
          fontWeight: 500,
          color: successRateColor(agent.successRate),
          width: 84,
          textAlign: "right",
          flexShrink: 0,
        }}
      >
        {agent.successRate}
      </div>

      {/* Toggle */}
      <div
        className={`toggle-switch ${agent._enabled ? "on" : "off"}`}
        onClick={onToggle}
        role="switch"
        aria-checked={agent._enabled}
        aria-label={`Toggle ${agent.name}`}
        style={{ flexShrink: 0 }}
      />
    </div>
  );
}

export function AgentsPanel() {
  const [enabledMap, setEnabledMap] = useState<Record<string, boolean>>(
    Object.fromEntries(AGENTS_STATIC.map((a) => [a.name, a.enabled]))
  );

  function toggle(name: string) {
    setEnabledMap((prev) => ({ ...prev, [name]: !prev[name] }));
  }

  return (
    <div className="officer-card" style={{ padding: "0 20px" }}>
      {/* Column header row */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 16,
          padding: "16px 0 8px",
          borderBottom: "1px solid rgba(12,18,34,0.06)",
        }}
      >
        {/* spacer for icon */}
        <div style={{ width: 40, flexShrink: 0 }} />

        {/* Agent */}
        <div
          style={{
            flex: 1,
            fontSize: 10,
            fontWeight: 600,
            textTransform: "uppercase",
            letterSpacing: "1px",
            color: "#B0A999",
          }}
        >
          Agent
        </div>

        {/* Latency */}
        <div
          style={{
            width: 52,
            fontSize: 10,
            fontWeight: 600,
            textTransform: "uppercase",
            letterSpacing: "1px",
            color: "#B0A999",
            textAlign: "right",
            flexShrink: 0,
          }}
        >
          Latency
        </div>

        {/* Success Rate */}
        <div
          style={{
            width: 84,
            fontSize: 10,
            fontWeight: 600,
            textTransform: "uppercase",
            letterSpacing: "1px",
            color: "#B0A999",
            textAlign: "right",
            flexShrink: 0,
          }}
        >
          Success
        </div>

        {/* Toggle header */}
        <div
          style={{
            width: 38,
            fontSize: 10,
            fontWeight: 600,
            textTransform: "uppercase",
            letterSpacing: "1px",
            color: "#B0A999",
            textAlign: "center",
            flexShrink: 0,
          }}
        >
          On
        </div>
      </div>

      {/* Agent rows */}
      {AGENTS_STATIC.map((agent, i) => (
        <AgentRow
          key={agent.name}
          agent={{ ...agent, _enabled: enabledMap[agent.name] ?? agent.enabled }}
          onToggle={() => toggle(agent.name)}
          isLast={i === AGENTS_STATIC.length - 1}
        />
      ))}
    </div>
  );
}
