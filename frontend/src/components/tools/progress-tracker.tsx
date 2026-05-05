"use client";

import { motion } from "framer-motion";
import { Card, CardContent } from "@/components/ui/card";

interface ProgressTrackerProps {
  data: Record<string, unknown>;
  onSubmit?: (payload: Record<string, unknown>) => void;
}

export function ProgressTracker({ data }: ProgressTrackerProps) {
  const currentStep = (data?.step as number) || (data?.current_step as number) || 1;
  const totalSteps = (data?.total as number) || (data?.total_steps as number) || 5;
  const label = (data?.label as string) || "";
  const percentage = Math.round((currentStep / totalSteps) * 100);

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      <Card className="shadow-sm">
        <CardContent className="pt-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-slate-700">
              Step {currentStep} of {totalSteps}
            </span>
            <span className="text-xs text-slate-400">{percentage}%</span>
          </div>

          <div className="relative h-2.5 w-full rounded-full bg-slate-100 overflow-hidden">
            <motion.div
              className="absolute inset-y-0 left-0 rounded-full"
              style={{
                background: "linear-gradient(90deg, #0F172A, #D4A853)",
              }}
              initial={{ width: 0 }}
              animate={{ width: `${percentage}%` }}
              transition={{ duration: 0.6, ease: "easeOut" }}
            />
          </div>

          {label && (
            <p className="mt-2 text-xs text-slate-500">{label}</p>
          )}
        </CardContent>
      </Card>
    </motion.div>
  );
}
