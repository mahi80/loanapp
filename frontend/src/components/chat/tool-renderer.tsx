"use client";

import { BasicInfoForm } from "@/components/tools/basic-info-form";
import { LoanDetailsForm } from "@/components/tools/loan-details-form";
import { DocUploadWidget } from "@/components/tools/doc-upload-widget";
import { VerificationCard } from "@/components/tools/verification-card";
import { ProgressTracker } from "@/components/tools/progress-tracker";
import { OfferCard } from "@/components/tools/offer-card";
import { DecisionCard } from "@/components/tools/decision-card";
import { EligibilityCard } from "@/components/tools/eligibility-card";

interface ToolRendererProps {
  toolName: string;
  data: Record<string, unknown>;
  onSubmit?: (payload: Record<string, unknown>) => void;
}

const toolMap: Record<
  string,
  React.ComponentType<{ data: Record<string, unknown>; onSubmit?: (payload: Record<string, unknown>) => void }>
> = {
  collect_basic_info: BasicInfoForm,
  collect_loan_details: LoanDetailsForm,
  upload_document: DocUploadWidget,
  show_verification: VerificationCard,
  show_progress: ProgressTracker,
  show_offer: OfferCard,
  show_decision: DecisionCard,
  show_eligibility: EligibilityCard,
};

export function ToolRenderer({ toolName, data, onSubmit }: ToolRendererProps) {
  const Component = toolMap[toolName];

  if (!Component) {
    return (
      <div className="rounded-lg border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-500">
        Unknown tool: <code className="font-mono text-xs">{toolName}</code>
      </div>
    );
  }

  return <Component data={data} onSubmit={onSubmit} />;
}
