"use client";

import { motion } from "framer-motion";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ShieldCheck, ShieldX } from "lucide-react";
import { cn } from "@/lib/utils";

interface EligibilityCardProps {
  data: Record<string, unknown>;
  onSubmit?: (payload: Record<string, unknown>) => void;
}

export function EligibilityCard({ data }: EligibilityCardProps) {
  const eligible = data?.eligible === true;
  const title = (data?.title as string) || "Eligibility Check";
  const message = (data?.message as string) || "";
  const criteria = (data?.criteria as Record<string, boolean>) || {};

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      <Card
        className={cn(
          "border-l-4 shadow-md",
          eligible ? "border-l-green-500" : "border-l-red-500"
        )}
      >
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-[#0F172A]">
            {eligible ? (
              <ShieldCheck className="w-5 h-5 text-green-500" />
            ) : (
              <ShieldX className="w-5 h-5 text-red-500" />
            )}
            {title}
          </CardTitle>
        </CardHeader>
        <CardContent>
          {message && (
            <p className="text-sm text-slate-600 mb-3">{message}</p>
          )}

          {Object.keys(criteria).length > 0 && (
            <div className="space-y-2">
              {Object.entries(criteria).map(([key, passed]) => (
                <div key={key} className="flex items-center gap-2">
                  <span
                    className={cn(
                      "w-2 h-2 rounded-full",
                      passed ? "bg-green-500" : "bg-red-500"
                    )}
                  />
                  <span className="text-sm text-slate-600">
                    {key.replace(/_/g, " ")}
                  </span>
                  <span
                    className={cn(
                      "ml-auto text-xs font-medium",
                      passed ? "text-green-600" : "text-red-600"
                    )}
                  >
                    {passed ? "Pass" : "Fail"}
                  </span>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </motion.div>
  );
}
