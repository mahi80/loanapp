import { ApplicationList } from "@/components/status/application-list";

export default function StatusPage() {
  return (
    <div className="flex-1 overflow-auto p-6">
      <div className="max-w-3xl mx-auto">
        <h1 className="text-2xl font-bold text-[#0F172A] mb-1">My Applications</h1>
        <p className="text-slate-500 text-sm mb-6">Track the progress of your loan applications</p>
        <ApplicationList />
      </div>
    </div>
  );
}
