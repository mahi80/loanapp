"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { User } from "lucide-react";

interface BasicInfoFormProps {
  data: Record<string, unknown>;
  onSubmit?: (payload: Record<string, unknown>) => void;
}

const employmentTypes = [
  { value: "salaried", label: "Salaried" },
  { value: "self_employed", label: "Self Employed" },
  { value: "business", label: "Business Owner" },
  { value: "professional", label: "Professional" },
];

export function BasicInfoForm({ data, onSubmit }: BasicInfoFormProps) {
  const [form, setForm] = useState({
    full_name: "",
    pan_number: "",
    date_of_birth: "",
    mobile: "",
    email: "",
    employment_type: "salaried",
    monthly_income: "",
    employer: "",
    city: "",
  });
  const [errors, setErrors] = useState<Record<string, string>>({});

  const validate = () => {
    const newErrors: Record<string, string> = {};
    if (!form.full_name.trim()) newErrors.full_name = "Full name is required";
    if (!/^[A-Z]{5}[0-9]{4}[A-Z]$/.test(form.pan_number))
      newErrors.pan_number = "Invalid PAN format (e.g. ABCDE1234F)";
    if (!form.date_of_birth) newErrors.date_of_birth = "Date of birth is required";
    if (!/^[6-9]\d{9}$/.test(form.mobile))
      newErrors.mobile = "Invalid 10-digit mobile number";
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email))
      newErrors.email = "Invalid email address";
    if (!form.monthly_income || Number(form.monthly_income) <= 0)
      newErrors.monthly_income = "Enter valid monthly income";
    if (!form.city.trim()) newErrors.city = "City is required";
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = () => {
    if (!validate()) return;
    onSubmit?.({
      tool: "collect_basic_info",
      ...form,
      monthly_income: Number(form.monthly_income),
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
            <User className="w-5 h-5 text-[#D4A853]" />
            {(data?.title as string) || "Personal Information"}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="space-y-1.5">
              <Label htmlFor="full_name">Full Name</Label>
              <Input
                id="full_name"
                value={form.full_name}
                onChange={(e) => update("full_name", e.target.value)}
                placeholder="As on PAN card"
              />
              {errors.full_name && (
                <p className="text-xs text-red-500">{errors.full_name}</p>
              )}
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="pan_number">PAN Number</Label>
              <Input
                id="pan_number"
                value={form.pan_number}
                onChange={(e) => update("pan_number", e.target.value.toUpperCase())}
                placeholder="ABCDE1234F"
                maxLength={10}
              />
              {errors.pan_number && (
                <p className="text-xs text-red-500">{errors.pan_number}</p>
              )}
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="date_of_birth">Date of Birth</Label>
              <Input
                id="date_of_birth"
                type="date"
                value={form.date_of_birth}
                onChange={(e) => update("date_of_birth", e.target.value)}
              />
              {errors.date_of_birth && (
                <p className="text-xs text-red-500">{errors.date_of_birth}</p>
              )}
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="mobile">Mobile Number</Label>
              <Input
                id="mobile"
                type="tel"
                value={form.mobile}
                onChange={(e) => update("mobile", e.target.value)}
                placeholder="9876543210"
                maxLength={10}
              />
              {errors.mobile && (
                <p className="text-xs text-red-500">{errors.mobile}</p>
              )}
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="email">Email Address</Label>
              <Input
                id="email"
                type="email"
                value={form.email}
                onChange={(e) => update("email", e.target.value)}
                placeholder="you@example.com"
              />
              {errors.email && (
                <p className="text-xs text-red-500">{errors.email}</p>
              )}
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="employment_type">Employment Type</Label>
              <select
                id="employment_type"
                value={form.employment_type}
                onChange={(e) => update("employment_type", e.target.value)}
                className="flex h-8 w-full rounded-lg border border-input bg-transparent px-2.5 py-1 text-sm outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50"
              >
                {employmentTypes.map((t) => (
                  <option key={t.value} value={t.value}>
                    {t.label}
                  </option>
                ))}
              </select>
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="monthly_income">Monthly Income</Label>
              <Input
                id="monthly_income"
                type="number"
                value={form.monthly_income}
                onChange={(e) => update("monthly_income", e.target.value)}
                placeholder="50000"
              />
              {errors.monthly_income && (
                <p className="text-xs text-red-500">{errors.monthly_income}</p>
              )}
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="employer">Employer / Business Name</Label>
              <Input
                id="employer"
                value={form.employer}
                onChange={(e) => update("employer", e.target.value)}
                placeholder="Company name"
              />
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="city">City</Label>
              <Input
                id="city"
                value={form.city}
                onChange={(e) => update("city", e.target.value)}
                placeholder="Mumbai"
              />
              {errors.city && (
                <p className="text-xs text-red-500">{errors.city}</p>
              )}
            </div>
          </div>

          <div className="mt-6 flex justify-end">
            <Button
              onClick={handleSubmit}
              className="bg-[#0F172A] hover:bg-[#1E293B] text-white px-6"
            >
              Submit Information
            </Button>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}
