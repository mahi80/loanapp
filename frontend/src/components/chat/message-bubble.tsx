"use client";

import { motion } from "framer-motion";
import { cn } from "@/lib/utils";

interface MessageBubbleProps {
  role: "user" | "assistant";
  children: React.ReactNode;
  userImage?: string | null;
  userName?: string | null;
}

export function MessageBubble({ role, children, userImage, userName }: MessageBubbleProps) {
  const isUser = role === "user";
  const initials = (userName || "U").split(" ").map(w => w[0]).join("").slice(0, 2).toUpperCase();

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, ease: "easeOut" }}
      className={cn("flex gap-3 max-w-3xl", isUser ? "ml-auto flex-row-reverse" : "")}
    >
      {/* Avatar */}
      {isUser ? (
        userImage ? (
          <div className="w-8 h-8 rounded-full shrink-0 mt-1 overflow-hidden border-2 border-slate-200">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src={userImage}
              alt={userName || ""}
              className="w-full h-full object-cover"
              referrerPolicy="no-referrer"
            />
          </div>
        ) : (
          <div className="w-8 h-8 rounded-full bg-[#0F172A] flex items-center justify-center shrink-0 mt-1">
            <span className="text-white text-xs font-bold">{initials}</span>
          </div>
        )
      ) : (
        <div className="w-8 h-8 rounded-full bg-[#D4A853] flex items-center justify-center shrink-0 mt-1">
          <span className="text-white text-xs font-bold">AI</span>
        </div>
      )}

      {/* Message content */}
      <div
        className={cn(
          "rounded-2xl px-4 py-3 max-w-[85%]",
          isUser
            ? "bg-[#0F172A] text-white rounded-tr-md"
            : "bg-white border border-slate-200 text-slate-800 rounded-tl-md shadow-sm"
        )}
      >
        {children}
      </div>
    </motion.div>
  );
}
