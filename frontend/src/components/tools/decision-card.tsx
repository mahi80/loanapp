"use client";

import { motion } from "framer-motion";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { CheckCircle2, XCircle, AlertTriangle, ArrowUpRight } from "lucide-react";
import { cn } from "@/lib/utils";

interface DecisionCardProps {
  data: Record<string, unknown>;
  onSubmit?: (payload: Record<string, unknown>) => void;
}

type DecisionStatus = "approved" | "conditional" | "denied" | "escalated";

const statusConfig: Record<
  DecisionStatus,
  { icon: React.ReactNode; borderColor: string; bgColor: string; label: string }
> = {
  approved: {
    icon: <CheckCircle2 className="w-6 h-6 text-green-600" />,
    borderColor: "border-l-green-500",
    bgColor: "bg-green-50",
    label: "Approved",
  },
  conditional: {
    icon: <AlertTriangle className="w-6 h-6 text-amber-600" />,
    borderColor: "border-l-amber-500",
    bgColor: "bg-amber-50",
    label: "Conditional Approval",
  },
  denied: {
    icon: <XCircle className="w-6 h-6 text-red-600" />,
    borderColor: "border-l-red-500",
    bgColor: "bg-red-50",
    label: "Denied",
  },
  escalated: {
    icon: <ArrowUpRight className="w-6 h-6 text-blue-600" />,
    borderColor: "border-l-blue-500",
    bgColor: "bg-blue-50",
    label: "Escalated for Review",
  },
};

export function DecisionCard({ data }: DecisionCardProps) {
  const status = ((data?.status as string) || "denied") as DecisionStatus;
  const reasons = (data?.reasons as string[]) || [];
  const confidence = data?.confidence as number | undefined;
  const config = statusConfig[status] || statusConfig.denied;

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
    >
      <Card className={cn("border-l-4 shadow-md", config.borderColor)}>
        <CardHeader className={config.bgColor}>
          <CardTitle className="flex items-center gap-3 text-[#0F172A]">
            {config.icon}
            <div>
              <p className="text-base font-semibold">{config.label}</p>
              {confidence != null && (
                <p className="text-xs font-normal text-slate-500">
                  Confidence: {confidence}%
                </p>
              )}
            </div>
          </CardTitle>
        </CardHeader>
        <CardContent>
          {reasons.length > 0 && (
            <div className="space-y-1.5">
              <p className="text-xs text-slate-400 uppercase tracking-wider mb-2">
                Reasons
              </p>
              <ul className="space-y-1.5">
                {reasons.map((reason, idx) => (
                  <li
                    key={idx}
                    className="flex items-start gap-2 text-sm text-slate-600"
                  >
                    <span className="mt-1.5 w-1.5 h-1.5 rounded-full bg-slate-400 shrink-0" />
                    {reason}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </CardContent>
      </Card>
    </motion.div>
  );
}
