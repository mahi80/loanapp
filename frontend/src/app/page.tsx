import { auth } from "@/auth";
import { redirect } from "next/navigation";
import Image from "next/image";
import { SignInButton } from "@/components/auth/sign-in-button";
import { HeroSection } from "@/components/hero/hero-section";
import { Shield, Zap, BarChart3 } from "lucide-react";

export default async function LandingPage() {
  const session = await auth();
  if (session) {
    if ((session as any).role === "officer") redirect("/dashboard");
    redirect("/chat");
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#0F172A] via-[#1E293B] to-[#0F172A] flex flex-col">
      {/* Header */}
      <header className="px-8 py-6 shrink-0">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <Image src="/images/logo-dark.svg" alt="LoanAI" width={140} height={40} priority />
        </div>
      </header>

      {/* Hero: text + 3D graph */}
      <section className="flex-1 flex items-center px-8 py-8">
        <div className="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-2 gap-12 items-center w-full">
          {/* Left: Text */}
          <div>
            <div className="inline-flex items-center gap-2 bg-[#D4A853]/10 border border-[#D4A853]/20 rounded-full px-4 py-1.5 mb-6">
              <span className="w-2 h-2 rounded-full bg-[#D4A853] animate-pulse" />
              <span className="text-[#D4A853] text-sm font-medium">AI-Powered Underwriting</span>
            </div>

            <h1 className="text-4xl md:text-6xl font-bold text-white mb-5 leading-tight">
              Personal Loans,<br />
              <span className="text-[#D4A853]">Intelligently Processed</span>
            </h1>

            <p className="text-base md:text-lg text-slate-400 mb-8 max-w-lg leading-relaxed">
              Apply for a personal loan with our AI-guided system. Upload documents,
              get instant verification, and receive a decision — all through a simple conversation.
            </p>

            <SignInButton />
          </div>

          {/* Right: 3D Agent Graph */}
          <div className="hidden lg:block">
            <HeroSection />
          </div>
        </div>
      </section>

      {/* Feature cards — normal flow, not absolute */}
      <section className="px-8 pb-10 shrink-0">
        <div className="max-w-5xl mx-auto grid grid-cols-1 md:grid-cols-3 gap-6">
          {[
            { icon: Zap, title: "Instant Verification", desc: "Documents verified in seconds using Azure AI" },
            { icon: Shield, title: "Bank-Grade Security", desc: "RBI-compliant with end-to-end encryption" },
            { icon: BarChart3, title: "Smart Assessment", desc: "13 AI agents analyze your application" },
          ].map(({ icon: Icon, title, desc }) => (
            <div key={title} className="bg-white/5 border border-white/10 rounded-2xl p-5 text-left backdrop-blur-sm hover:bg-white/10 transition-colors">
              <div className="w-9 h-9 rounded-lg bg-[#D4A853]/20 flex items-center justify-center mb-3">
                <Icon className="w-4 h-4 text-[#D4A853]" />
              </div>
              <h3 className="text-white font-semibold text-sm mb-1">{title}</h3>
              <p className="text-slate-400 text-xs">{desc}</p>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
