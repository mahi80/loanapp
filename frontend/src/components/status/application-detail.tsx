"use client";

import { useEffect, useState, useCallback } from "react";
import { useSession } from "next-auth/react";
import Link from "next/link";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ArrowLeft, MessageSquare, FileText, Clock, CheckCircle, XCircle, AlertCircle } from "lucide-react";
import { apiClient } from "@/lib/api";
import { PhaseStepper } from "./phase-stepper";
import { StatusCard } from "./status-card";

const INR = new Intl.NumberFormat("en-IN", {
  style: "currency",
  currency: "INR",
  maximumFractionDigits: 0,
});

interface ApplicationData {
  application_id: string;
  reference_number: string;
  loan_type: string;
  loan_amount: number;
  tenure_months: number;
  created_at: string;
  current_phase: string;
  completed_phases: string[];
  decision: string | null;
  offer: Record<string, unknown> | null;
  denial_reasons: string[];
  conversation_id: string | null;
  document_count: number;
}

interface ApplicationDetailProps {
  applicationId: string;
}

export function ApplicationDetail({ applicationId }: ApplicationDetailProps) {
  const { data: session } = useSession();
  const [data, setData] = useState<ApplicationData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    if (!session) return;
    const token = (session as any)?.backendToken as string;
    try {
      const result = await apiClient(`/api/v1/status/applications/${applicationId}`, { token });
      setData(result);
      setError(null);
    } catch (err) {
      setError("Failed to load application details.");
    }
  }, [session, applicationId]);

  useEffect(() => {
    fetchData().finally(() => setLoading(false));
  }, [fetchData]);

  // Poll every 15s while no decision
  useEffect(() => {
    if (!data || data.decision) return;
    const interval = setInterval(fetchData, 15_000);
    return () => clearInterval(interval);
  }, [data, fetchData]);

  if (loading) {
    return (
      <div className="p-12 text-center text-slate-400">
        Loading application...
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="p-12 text-center">
        <p className="text-red-500 mb-4">{error || "Application not found."}</p>
        <Link href="/status" className="text-sm text-[#0F172A] underline">
          Back to My Applications
        </Link>
      </div>
    );
  }

  // Determine banner config based on decision
  const getBannerConfig = () => {
    switch (data.decision) {
      case "approved":
        return {
          bg: "bg-[#E8F5EE]",
          border: "border-[#2E8B57]/20",
          icon: <CheckCircle className="w-6 h-6 text-[#2E8B57]" />,
          title: "Your loan has been approved!",
          titleColor: "text-[#1B6B3A]",
          subtitle: "Check your offer details below",
          subtitleColor: "text-[#2E8B57]/70",
          linkColor: "text-[#2E8B57]",
        };
      case "denied":
        return {
          bg: "bg-[#FCEAEA]",
          border: "border-[#C0392B]/20",
          icon: <XCircle className="w-6 h-6 text-[#C0392B]" />,
          title: "Your application was not approved",
          titleColor: "text-[#922020]",
          subtitle: "Please review the details below",
          subtitleColor: "text-[#C0392B]/70",
          linkColor: "text-[#C0392B]",
        };
      case "conditional":
        return {
          bg: "bg-[#E8F0FE]",
          border: "border-[#3B7DDD]/20",
          icon: <AlertCircle className="w-6 h-6 text-[#3B7DDD]" />,
          title: "Your loan is conditionally approved",
          titleColor: "text-[#1A56B8]",
          subtitle: "Additional steps may be required",
          subtitleColor: "text-[#3B7DDD]/70",
          linkColor: "text-[#3B7DDD]",
        };
      default:
        return null;
    }
  };

  const bannerConfig = getBannerConfig();

  return (
    <div className="space-y-6">
      {/* Decision banner */}
      {bannerConfig && (
        <div className={`flex items-center gap-3 p-4 rounded-[12px] border ${bannerConfig.bg} ${bannerConfig.border}`}>
          {bannerConfig.icon}
          <div className="flex-1">
            <p className={`font-semibold text-base ${bannerConfig.titleColor}`}>
              {bannerConfig.title}
            </p>
            <p className={`text-xs ${bannerConfig.subtitleColor}`}>
              {bannerConfig.subtitle}
            </p>
          </div>
          <Link href={data?.conversation_id ? `/chat/${data.conversation_id}` : "/chat"} className={`font-medium underline ${bannerConfig.linkColor}`}>
            View Chat
          </Link>
        </div>
      )}

      {/* Back link + title */}
      <div>
        <Link
          href="/status"
          className="inline-flex items-center gap-1.5 text-sm text-slate-500 hover:text-slate-800 transition-colors mb-3"
        >
          <ArrowLeft className="w-4 h-4" />
          My Applications
        </Link>
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-[#0F172A]">
              {data.reference_number || data.application_id.slice(0, 8).toUpperCase()}
            </h1>
            <p className="text-slate-500 text-sm capitalize">
              {data.loan_type || "Personal Loan"} &bull; Applied{" "}
              {new Date(data.created_at).toLocaleDateString("en-IN", {
                day: "2-digit",
                month: "short",
                year: "numeric",
              })}
            </p>
          </div>
          {data.conversation_id && (
            <Link href={`/chat/${data.conversation_id}`}>
              <Button className="bg-[#0F172A] hover:bg-[#1e293b] text-white gap-2">
                <MessageSquare className="w-4 h-4" />
                Open Conversation
              </Button>
            </Link>
          )}
        </div>
      </div>

      {/* Phase stepper */}
      <Card>
        <CardContent className="pt-6 pb-8 px-6">
          <h2 className="text-sm font-semibold text-slate-500 uppercase tracking-wider mb-6">
            Application Progress
          </h2>
          <PhaseStepper
            completedPhases={data.completed_phases}
            currentPhase={data.current_phase}
            decision={data.decision}
          />
        </CardContent>
      </Card>

      {/* Status card */}
      <StatusCard
        decision={data.decision}
        offer={data.offer}
        reasons={data.denial_reasons || []}
        loanAmount={data.loan_amount}
      />

      {/* Quick stats */}
      <div className="grid grid-cols-3 gap-3">
        {[
          {
            icon: <FileText className="w-5 h-5 text-[#D4A853]" />,
            label: "Loan Amount",
            value: INR.format(data.loan_amount),
          },
          {
            icon: <Clock className="w-5 h-5 text-[#D4A853]" />,
            label: "Tenure",
            value: data.tenure_months ? `${data.tenure_months} months` : "—",
          },
          {
            icon: <FileText className="w-5 h-5 text-[#D4A853]" />,
            label: "Documents",
            value: `${data.document_count ?? 0} uploaded`,
          },
        ].map(({ icon, label, value }) => (
          <Card key={label}>
            <CardContent className="py-4 flex items-center gap-3">
              <div className="w-9 h-9 rounded-xl bg-[#D4A853]/10 flex items-center justify-center shrink-0">
                {icon}
              </div>
              <div>
                <p className="text-xs text-slate-500">{label}</p>
                <p className="text-sm font-semibold text-[#0F172A]">{value}</p>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
