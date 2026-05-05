import { auth } from "@/auth";
import { redirect } from "next/navigation";
import Image from "next/image";
import Link from "next/link";
import { ProfileMenu } from "@/components/auth/profile-menu";
import { NotificationBell } from "@/components/notifications/notification-bell";

export default async function StatusLayout({ children }: { children: React.ReactNode }) {
  const session = await auth();
  if (!session) redirect("/");
  if ((session as any).role === "officer") redirect("/dashboard");

  return (
    <div className="h-screen flex flex-col bg-[#FAFBFC]">
      <header className="h-16 border-b border-slate-200 bg-white flex items-center px-6 shrink-0">
        <Image src="/images/logo-light.svg" alt="LoanAI" width={120} height={32} />
        <nav className="ml-8 flex items-center gap-6">
          <Link href="/chat" className="text-sm text-slate-500 hover:text-slate-800 transition-colors">Chat</Link>
          <Link href="/status" className="text-sm text-[#0F172A] font-semibold border-b-2 border-[#D4A853] pb-0.5">My Applications</Link>
          {(session as any).role === "officer" && (
            <Link href="/dashboard" className="text-sm text-[#D4A853] font-semibold hover:text-[#C8A24E] transition-colors">Officer Dashboard</Link>
          )}
        </nav>
        <div className="ml-auto flex items-center gap-3">
          <NotificationBell />
          <ProfileMenu name={session.user?.name} email={session.user?.email} image={session.user?.image} />
        </div>
      </header>
      {children}
    </div>
  );
}
