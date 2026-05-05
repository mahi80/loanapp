import { auth } from "@/auth";
import { redirect } from "next/navigation";
import { DM_Serif_Display, DM_Sans, JetBrains_Mono } from "next/font/google";
import "@/components/officer/officer.css";

const dmSerifDisplay = DM_Serif_Display({
  weight: "400",
  subsets: ["latin"],
  variable: "--font-dm-serif",
});

const dmSans = DM_Sans({
  subsets: ["latin"],
  variable: "--font-dm-sans",
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-jetbrains-mono",
});

export default async function DashboardLayout({ children }: { children: React.ReactNode }) {
  const session = await auth();
  if (!session) redirect("/");

  return (
    <div
      className={`officer-dashboard min-h-screen bg-[#E8E2D6] ${dmSerifDisplay.variable} ${dmSans.variable} ${jetbrainsMono.variable}`}
    >
      {children}
    </div>
  );
}
