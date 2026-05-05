"use client";

import { Check, X } from "lucide-react";

interface PhaseStepperProps {
  completedPhases: string[];
  currentPhase: string;
  decision: string | null;
}

const PHASES = [
  { key: "intake", label: "Info" },
  { key: "doc_collection", label: "Docs" },
  { key: "doc_verification", label: "AI Check" },
  { key: "human_review", label: "Review" },
  { key: "decision", label: "Decision" },
];

export function PhaseStepper({ completedPhases, currentPhase, decision }: PhaseStepperProps) {
  return (
    <div className="flex items-start justify-between w-full">
      {PHASES.map((phase, index) => {
        const isCompleted = completedPhases.includes(phase.key);
        const isCurrent = currentPhase === phase.key;
        const isDenied = phase.key === "decision" && decision === "denied";
        const isLast = index === PHASES.length - 1;

        let circleClass = "w-9 h-9 rounded-full flex items-center justify-center text-sm font-semibold border-2 transition-all ";
        if (isDenied) {
          circleClass += "bg-red-100 border-red-500 text-red-600";
        } else if (isCompleted) {
          circleClass += "bg-[#22c55e] border-[#22c55e] text-white";
        } else if (isCurrent) {
          circleClass += "bg-[#D4A853] border-[#D4A853] text-white ring-4 ring-[#D4A853]/30";
        } else {
          circleClass += "bg-white border-slate-200 text-slate-400";
        }

        return (
          <div key={phase.key} className="flex items-start flex-1">
            <div className="flex flex-col items-center">
              <div className={circleClass}>
                {isDenied ? (
                  <X className="w-4 h-4" />
                ) : isCompleted ? (
                  <Check className="w-4 h-4" />
                ) : (
                  <span>{index + 1}</span>
                )}
              </div>
              <span
                className={`mt-2 text-xs font-medium text-center whitespace-nowrap ${
                  isCurrent
                    ? "text-[#D4A853]"
                    : isCompleted
                    ? "text-[#22c55e]"
                    : isDenied
                    ? "text-red-500"
                    : "text-slate-400"
                }`}
              >
                {phase.label}
              </span>
            </div>

            {!isLast && (
              <div
                className={`flex-1 h-0.5 mt-4 mx-1 transition-all ${
                  isCompleted ? "bg-[#22c55e]" : "bg-slate-200"
                }`}
              />
            )}
          </div>
        );
      })}
    </div>
  );
}
