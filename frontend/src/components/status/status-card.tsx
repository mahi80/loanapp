"use client";

const INR = new Intl.NumberFormat("en-IN", {
  style: "currency",
  currency: "INR",
  maximumFractionDigits: 0,
});

interface Offer {
  approved_amount?: number;
  interest_rate?: number;
  tenure_months?: number;
  emi?: number;
  total_interest?: number;
  [key: string]: unknown;
}

interface StatusCardProps {
  decision: string | null;
  offer: Offer | null;
  reasons: string[];
  loanAmount: number;
}

export function StatusCard({ decision, offer, reasons, loanAmount }: StatusCardProps) {
  if (!decision || decision === "under_review" || decision === "pending") {
    return (
      <div className="rounded-2xl border border-[#fde68a] bg-gradient-to-br from-[#fefce8] to-[#fff7ed] p-6">
        <div className="flex items-start gap-4">
          <span className="text-3xl">⏳</span>
          <div>
            <h3 className="text-lg font-semibold text-amber-900 mb-1">Under Officer Review</h3>
            <p className="text-sm text-amber-700">
              Your application is being reviewed by a loan officer. This typically takes 1–2 business days.
              You&apos;ll be notified once a decision is made.
            </p>
          </div>
        </div>
      </div>
    );
  }

  if (decision === "approved" || decision === "conditional") {
    const approvedAmount = offer?.approved_amount ?? loanAmount;
    const emi = offer?.emi;
    const totalInterest = offer?.total_interest;
    const rate = offer?.interest_rate;
    const tenure = offer?.tenure_months;

    return (
      <div className="rounded-2xl border border-[#86efac] bg-gradient-to-br from-[#f0fdf4] to-[#ecfdf5] p-6">
        <div className="flex items-start gap-4 mb-5">
          <span className="text-3xl">🎉</span>
          <div>
            <h3 className="text-lg font-semibold text-green-900 mb-1">Loan Approved!</h3>
            <p className="text-sm text-green-700">
              Congratulations! Your loan application has been approved.
              {decision === "conditional" && " Some conditions may apply — review your offer carefully."}
            </p>
          </div>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-5">
          {[
            { label: "Approved Amount", value: INR.format(approvedAmount) },
            { label: "Interest Rate", value: rate ? `${rate}% p.a.` : "—" },
            { label: "Monthly EMI", value: emi ? INR.format(emi) : "—" },
            { label: "Total Interest", value: totalInterest ? INR.format(totalInterest) : "—" },
          ].map(({ label, value }) => (
            <div key={label} className="bg-white/60 rounded-xl p-3">
              <p className="text-xs text-green-600 font-medium mb-0.5">{label}</p>
              <p className="text-sm font-semibold text-green-900">{value}</p>
            </div>
          ))}
        </div>

        {tenure && (
          <p className="text-xs text-green-600 mb-4">Tenure: {tenure} months</p>
        )}

        <button className="w-full py-2.5 rounded-xl bg-[#22c55e] text-white font-semibold text-sm hover:bg-green-600 transition-colors">
          Accept Offer
        </button>
      </div>
    );
  }

  if (decision === "denied") {
    return (
      <div className="rounded-2xl border border-[#fca5a5] bg-gradient-to-br from-[#fef2f2] to-[#fff1f2] p-6">
        <div className="flex items-start gap-4 mb-4">
          <span className="text-3xl">📋</span>
          <div>
            <h3 className="text-lg font-semibold text-red-900 mb-1">Application Not Approved</h3>
            <p className="text-sm text-red-700">
              We regret to inform you that we are unable to approve your loan application at this time.
            </p>
          </div>
        </div>

        {reasons.length > 0 && (
          <div className="bg-white/60 rounded-xl p-4 mb-4">
            <p className="text-xs font-semibold text-red-700 uppercase tracking-wider mb-2">Reasons</p>
            <ul className="space-y-1">
              {reasons.map((reason, i) => (
                <li key={i} className="flex items-start gap-2 text-sm text-red-800">
                  <span className="mt-0.5 text-red-400">•</span>
                  {reason}
                </li>
              ))}
            </ul>
          </div>
        )}

        <p className="text-xs text-red-600">
          You may re-apply after 6 months or after addressing the above concerns. Contact our support team for guidance.
        </p>
      </div>
    );
  }

  return null;
}
