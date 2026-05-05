"use client";

import { motion } from "framer-motion";
import { IndianRupee, Percent, Calendar, Receipt } from "lucide-react";

interface OfferCardProps {
  data: Record<string, unknown>;
  onSubmit?: (payload: Record<string, unknown>) => void;
}

function formatCurrency(value: unknown): string {
  const num = Number(value);
  if (isNaN(num)) return "--";
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(num);
}

export function OfferCard({ data }: OfferCardProps) {
  const loanAmount = data?.loan_amount;
  const interestRate = data?.interest_rate;
  const emi = data?.emi;
  const tenure = data?.tenure;
  const processingFee = data?.processing_fee;
  const totalCost = data?.total_cost;

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
    >
      <div className="rounded-2xl overflow-hidden shadow-lg">
        {/* Header */}
        <div className="bg-gradient-to-br from-[#0F172A] to-[#1E293B] px-6 py-5">
          <div className="flex items-center justify-between mb-4">
            <span className="text-sm text-slate-300">Loan Offer</span>
            <span className="inline-flex items-center rounded-full bg-[#D4A853]/20 px-3 py-0.5 text-xs font-semibold text-[#D4A853] ring-1 ring-[#D4A853]/30">
              Approved
            </span>
          </div>
          <p className="text-3xl font-bold text-white tracking-tight">
            {formatCurrency(loanAmount)}
          </p>
        </div>

        {/* Details grid */}
        <div className="bg-gradient-to-br from-[#0F172A]/95 to-[#1E293B] px-6 py-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="flex items-start gap-2">
              <Percent className="w-4 h-4 text-[#D4A853] mt-0.5 shrink-0" />
              <div>
                <p className="text-xs text-slate-400">Interest Rate</p>
                <p className="text-sm font-semibold text-white">
                  {interestRate != null ? `${interestRate}% p.a.` : "--"}
                </p>
              </div>
            </div>

            <div className="flex items-start gap-2">
              <IndianRupee className="w-4 h-4 text-[#D4A853] mt-0.5 shrink-0" />
              <div>
                <p className="text-xs text-slate-400">Monthly EMI</p>
                <p className="text-sm font-semibold text-white">
                  {formatCurrency(emi)}
                </p>
              </div>
            </div>

            <div className="flex items-start gap-2">
              <Calendar className="w-4 h-4 text-[#D4A853] mt-0.5 shrink-0" />
              <div>
                <p className="text-xs text-slate-400">Tenure</p>
                <p className="text-sm font-semibold text-white">
                  {tenure != null ? `${tenure} months` : "--"}
                </p>
              </div>
            </div>

            <div className="flex items-start gap-2">
              <Receipt className="w-4 h-4 text-[#D4A853] mt-0.5 shrink-0" />
              <div>
                <p className="text-xs text-slate-400">Processing Fee</p>
                <p className="text-sm font-semibold text-white">
                  {formatCurrency(processingFee)}
                </p>
              </div>
            </div>
          </div>

          {totalCost != null && (
            <div className="mt-4 pt-3 border-t border-white/10 flex items-center justify-between">
              <span className="text-xs text-slate-400">Total Cost of Loan</span>
              <span className="text-sm font-bold text-[#D4A853]">
                {formatCurrency(totalCost)}
              </span>
            </div>
          )}
        </div>
      </div>
    </motion.div>
  );
}
