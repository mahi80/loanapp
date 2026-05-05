"use client";

import { useEffect, useState } from "react";
import { useSession } from "next-auth/react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import Link from "next/link";
import { FileText, ArrowRight } from "lucide-react";
import { apiClient } from "@/lib/api";

interface Application {
  application_id: string;
  reference_number: string;
  loan_type: string;
  created_at: string;
  loan_amount: number;
  status: string;
  decision: string | null;
}

const INR = new Intl.NumberFormat("en-IN", {
  style: "currency",
  currency: "INR",
  maximumFractionDigits: 0,
});

function statusBadge(decision: string | null) {
  if (decision === "approved" || decision === "conditional") {
    return (
      <Badge className="bg-green-100 text-green-700 border-green-200 border">
        Approved
      </Badge>
    );
  }
  if (decision === "denied") {
    return (
      <Badge className="bg-red-100 text-red-700 border-red-200 border">
        Denied
      </Badge>
    );
  }
  return (
    <Badge className="bg-amber-100 text-amber-700 border-amber-200 border">
      Under Review
    </Badge>
  );
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });
}

export function ApplicationList() {
  const { data: session } = useSession();
  const [apps, setApps] = useState<Application[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!session) return;
    const token = (session as any)?.backendToken as string;
    apiClient("/api/v1/status/applications", { token })
      .then((data) => setApps(data.applications || []))
      .catch(() => setApps([]))
      .finally(() => setLoading(false));
  }, [session]);

  if (loading) {
    return (
      <div className="p-8 text-center text-slate-400">
        Loading applications...
      </div>
    );
  }

  if (apps.length === 0) {
    return (
      <Card>
        <CardContent className="py-16 text-center">
          <FileText className="w-10 h-10 text-slate-300 mx-auto mb-4" />
          <p className="text-slate-600 font-medium mb-1">No applications yet</p>
          <p className="text-slate-400 text-sm mb-6">
            Start a conversation to apply for a loan
          </p>
          <Link
            href="/chat"
            className="inline-flex items-center gap-2 text-sm font-medium text-[#0F172A] bg-[#D4A853]/10 hover:bg-[#D4A853]/20 px-4 py-2 rounded-lg transition-colors"
          >
            Go to Chat
            <ArrowRight className="w-4 h-4" />
          </Link>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-3">
      {apps.map((app) => (
        <Link key={app.application_id} href={`/status/${app.application_id}`}>
          <Card className="hover:border-[#D4A853]/50 hover:shadow-md transition-all cursor-pointer">
            <CardContent className="flex items-center gap-4 py-4">
              <div className="w-10 h-10 rounded-xl bg-[#0F172A]/5 flex items-center justify-center shrink-0">
                <FileText className="w-5 h-5 text-[#0F172A]" />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-0.5">
                  <p className="font-semibold text-sm text-[#0F172A]">
                    {app.reference_number || app.application_id.slice(0, 8).toUpperCase()}
                  </p>
                  <span className="text-xs text-slate-400">&bull;</span>
                  <p className="text-xs text-slate-500 capitalize">
                    {app.loan_type || "Personal Loan"}
                  </p>
                </div>
                <p className="text-xs text-slate-400">
                  Applied {formatDate(app.created_at)}
                </p>
              </div>
              <div className="flex items-center gap-3 shrink-0">
                <span className="text-sm font-semibold text-[#0F172A]">
                  {INR.format(app.loan_amount)}
                </span>
                {statusBadge(app.decision)}
                <ArrowRight className="w-4 h-4 text-slate-400" />
              </div>
            </CardContent>
          </Card>
        </Link>
      ))}
    </div>
  );
}
