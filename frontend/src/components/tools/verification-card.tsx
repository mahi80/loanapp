"use client";

import { motion } from "framer-motion";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { CheckCircle2, XCircle } from "lucide-react";
import { cn } from "@/lib/utils";

interface VerificationCardProps {
  data: Record<string, unknown>;
  onSubmit?: (payload: Record<string, unknown>) => void;
}

export function VerificationCard({ data }: VerificationCardProps) {
  const verified = data?.verified === true;
  const title = (data?.title as string) || "Verification";
  const extractedData = (data?.extracted_data as Record<string, string>) || {};
  const message = (data?.message as string) || "";

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      <Card
        className={cn(
          "border-l-4 shadow-md",
          verified ? "border-l-green-500" : "border-l-red-500"
        )}
      >
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-[#0F172A]">
            {verified ? (
              <CheckCircle2 className="w-5 h-5 text-green-500" />
            ) : (
              <XCircle className="w-5 h-5 text-red-500" />
            )}
            {title}
          </CardTitle>
        </CardHeader>
        <CardContent>
          {message && (
            <p className="text-sm text-slate-600 mb-3">{message}</p>
          )}

          {Object.keys(extractedData).length > 0 && (
            <div className="grid grid-cols-2 gap-x-6 gap-y-2">
              {Object.entries(extractedData).map(([key, value]) => (
                <div key={key} className="flex flex-col">
                  <span className="text-xs text-slate-400 uppercase tracking-wider">
                    {key.replace(/_/g, " ")}
                  </span>
                  <span className="text-sm font-medium text-slate-700">
                    {value}
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
