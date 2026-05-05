"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Banknote } from "lucide-react";

interface LoanDetailsFormProps {
  data: Record<string, unknown>;
  onSubmit?: (payload: Record<string, unknown>) => void;
}

const tenureOptions = [
  { value: "12", label: "12 months" },
  { value: "24", label: "24 months" },
  { value: "36", label: "36 months" },
  { value: "48", label: "48 months" },
  { value: "60", label: "60 months" },
];

const loanTypes = [
  { value: "personal", label: "Personal Loan" },
  { value: "home", label: "Home Loan" },
  { value: "auto", label: "Auto Loan" },
  { value: "business", label: "Business Loan" },
];

export function LoanDetailsForm({ data, onSubmit }: LoanDetailsFormProps) {
  const [form, setForm] = useState({
    loan_amount: "",
    tenure: "36",
    loan_type: "personal",
  });
  const [errors, setErrors] = useState<Record<string, string>>({});

  const validate = () => {
    const newErrors: Record<string, string> = {};
    const amount = Number(form.loan_amount);
    if (!form.loan_amount || amount <= 0) {
      newErrors.loan_amount = "Enter a valid loan amount";
    } else if (amount < 50000) {
      newErrors.loan_amount = "Minimum loan amount is 50,000";
    } else if (amount > 5000000) {
      newErrors.loan_amount = "Maximum loan amount is 50,00,000";
    }
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = () => {
    if (!validate()) return;
    onSubmit?.({
      tool: "collect_loan_details",
      loan_amount: Number(form.loan_amount),
      tenure: Number(form.tenure),
      loan_type: form.loan_type,
    });
  };

  const update = (field: string, value: string) => {
    setForm((prev) => ({ ...prev, [field]: value }));
    if (errors[field]) setErrors((prev) => ({ ...prev, [field]: "" }));
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      <Card className="border-l-4 border-l-[#D4A853] shadow-md">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-[#0F172A]">
            <Banknote className="w-5 h-5 text-[#D4A853]" />
            {(data?.title as string) || "Loan Details"}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="space-y-1.5 sm:col-span-2">
              <Label htmlFor="loan_amount">Loan Amount</Label>
              <Input
                id="loan_amount"
                type="number"
                value={form.loan_amount}
                onChange={(e) => update("loan_amount", e.target.value)}
                placeholder="500000"
              />
              {errors.loan_amount && (
                <p className="text-xs text-red-500">{errors.loan_amount}</p>
              )}
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="tenure">Tenure</Label>
              <select
                id="tenure"
                value={form.tenure}
                onChange={(e) => update("tenure", e.target.value)}
                className="flex h-8 w-full rounded-lg border border-input bg-transparent px-2.5 py-1 text-sm outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50"
              >
                {tenureOptions.map((t) => (
                  <option key={t.value} value={t.value}>
                    {t.label}
                  </option>
                ))}
              </select>
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="loan_type">Loan Type</Label>
              <select
                id="loan_type"
                value={form.loan_type}
                onChange={(e) => update("loan_type", e.target.value)}
                className="flex h-8 w-full rounded-lg border border-input bg-transparent px-2.5 py-1 text-sm outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50"
              >
                {loanTypes.map((t) => (
                  <option key={t.value} value={t.value}>
                    {t.label}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="mt-6 flex justify-end">
            <Button
              onClick={handleSubmit}
              className="bg-[#0F172A] hover:bg-[#1E293B] text-white px-6"
            >
              Submit Loan Details
            </Button>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}
