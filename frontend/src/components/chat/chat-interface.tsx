"use client";

import { useChat } from "@ai-sdk/react";
import { DefaultChatTransport } from "ai";
import { useSession } from "next-auth/react";
import { useRef, useEffect, useMemo, useState, useCallback } from "react";
import { motion } from "framer-motion";
import { FileText, MessageSquareText, BadgeDollarSign, ShieldCheck } from "lucide-react";
import { MessageBubble } from "./message-bubble";
import { ChatInput } from "./chat-input";
import { ToolRenderer } from "./tool-renderer";
import { MarkdownContent } from "./markdown-content";

const SUGGESTIONS = [
  {
    icon: BadgeDollarSign,
    title: "Apply for a Loan",
    description: "Start a new personal loan application with guided steps",
    message: "I'd like to apply for a personal loan",
  },
  {
    icon: FileText,
    title: "Document Guidance",
    description: "Learn what documents you'll need for your application",
    message: "What documents do I need for a loan application?",
  },
  {
    icon: MessageSquareText,
    title: "Loan Products",
    description: "Explore available loan types, rates, and eligibility",
    message: "What loan products do you offer?",
  },
  {
    icon: ShieldCheck,
    title: "Application Support",
    description: "Get help with an existing application or check status",
    message: "I need help with my existing application",
  },
];

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface ChatInterfaceProps {
  conversationId?: string;
}

export function ChatInterface({ conversationId: initialConversationId }: ChatInterfaceProps) {
  const { data: session } = useSession();
  const scrollRef = useRef<HTMLDivElement>(null);
  const sessionRef = useRef(session);
  useEffect(() => { sessionRef.current = session; }, [session]);

  // Track conversation_id across messages so the backend resumes the same thread
  const [convId, setConvId] = useState<string | undefined>(initialConversationId);
  const convIdRef = useRef(convId);
  useEffect(() => { convIdRef.current = convId; }, [convId]);

  const transport = useMemo(
    () =>
      new DefaultChatTransport({
        api: `${API_URL}/api/v1/chat/stream`,
        headers: () => ({
          Authorization: `Bearer ${(sessionRef.current as any)?.backendToken || ""}`,
        }),
        body: () => (convIdRef.current ? { conversation_id: convIdRef.current } : {}),
      }),
    []
  );

  const { messages, sendMessage, status } = useChat({ transport });


  const isStreaming = status === "streaming" || status === "submitted";

  // Extract conversation_id from META markers in assistant messages
  useEffect(() => {
    if (convId) return; // Already have one
    for (const msg of messages) {
      if (msg.role !== "assistant") continue;
      for (const part of msg.parts) {
        if (part.type === "text") {
          const text = (part as any).text as string;
          const match = text.match(/<<META:conversation_id:([^>]+)>>/);
          if (match) {
            setConvId(match[1]);
            return;
          }
        }
      }
    }
  }, [messages, convId]);

  // No auto-message — user starts the conversation themselves

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  // Serialize non-upload tool submissions so concurrent form/tool submits
  // don't open multiple in-flight /chat/stream requests.
  const [toolQueue, setToolQueue] = useState<Record<string, unknown>[]>([]);

  useEffect(() => {
    if (toolQueue.length === 0) return;
    if (isStreaming) return; // wait for current stream to finish
    const [next, ...rest] = toolQueue;
    setToolQueue(rest);
    sendMessage({ text: JSON.stringify(next) });
  }, [toolQueue, isStreaming, sendMessage]);

  // Batch document uploads — accumulate per-widget upload_document payloads
  // until all expected documents (from the latest assistant message's
  // upload_document tool markers) are uploaded, then emit ONE
  // `documents_submitted` message. This matches doc_collection_node's
  // interrupt contract and avoids per-doc agent replies + LangGraph races.
  const [docBatch, setDocBatch] = useState<Record<string, { file_name: string; document_id: string }>>({});

  // Parse latest assistant message for outstanding upload_document tool markers.
  const expectedDocTypes = useMemo(() => {
    for (let i = messages.length - 1; i >= 0; i--) {
      const msg = messages[i];
      if (msg.role !== "assistant") continue;
      const types = new Set<string>();
      for (const part of msg.parts) {
        if (part.type !== "text") continue;
        const text = (part as any).text as string;
        const matches = text.matchAll(/<<TOOL:upload_document:([^>]+)>>/g);
        for (const m of matches) {
          try {
            const parsed = JSON.parse(m[1]);
            if (typeof parsed.document_type === "string") types.add(parsed.document_type);
          } catch { /* ignore malformed marker */ }
        }
      }
      if (types.size > 0) return Array.from(types);
    }
    return [] as string[];
  }, [messages]);

  // When every expected doc has been uploaded, emit the batched submission.
  useEffect(() => {
    if (expectedDocTypes.length === 0) return;
    const uploadedTypes = Object.keys(docBatch);
    const allDone = expectedDocTypes.every((t) => uploadedTypes.includes(t));
    if (!allDone) return;
    const documents = expectedDocTypes.map((t) => ({
      document_type: t,
      file_name: docBatch[t].file_name,
      document_id: docBatch[t].document_id,
    }));
    setDocBatch({}); // reset for any subsequent re-upload round
    sendMessage({ text: JSON.stringify({ tool: "documents_submitted", documents }) });
  }, [docBatch, expectedDocTypes, sendMessage]);

  const handleToolSubmit = useCallback((payload: Record<string, unknown>) => {
    if (
      payload.tool === "upload_document" &&
      typeof payload.document_type === "string"
    ) {
      // Batch — don't send a chat message per upload.
      setDocBatch((b) => ({
        ...b,
        [payload.document_type as string]: {
          file_name: (payload.file_name as string) || "",
          document_id: (payload.document_id as string) || "",
        },
      }));
      return;
    }
    // Non-upload tools (forms etc.) keep the serialized queue behavior.
    setToolQueue((q) => [...q, payload]);
  }, []);

  const uploadBatchActive = expectedDocTypes.length > 0 && Object.keys(docBatch).length < expectedDocTypes.length;

  return (
    <div className="flex-1 flex flex-col overflow-hidden">
      <div ref={scrollRef} className="flex-1 overflow-y-auto px-6 py-4">
        <div className="max-w-3xl mx-auto space-y-6">
          {messages.length === 0 && !isStreaming && (
            <div className="flex flex-col items-center justify-center py-16">
              {/* Gold accent bar */}
              <motion.div
                initial={{ scaleX: 0 }}
                animate={{ scaleX: 1 }}
                transition={{ duration: 0.6, ease: "easeOut" }}
                className="w-12 h-1 bg-[#D4A853] rounded-full mb-6"
              />

              {/* Greeting */}
              <motion.h2
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: 0.15 }}
                className="text-2xl font-semibold text-[#0F172A] tracking-tight"
              >
                Welcome{session?.user?.name ? `, ${session.user.name.split(" ")[0]}` : ""}
              </motion.h2>

              <motion.p
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: 0.25 }}
                className="mt-2 text-sm text-slate-500 text-center max-w-md leading-relaxed"
              >
                I'm your AI loan advisor. I can guide you through the entire application
                process — from eligibility to approval.
              </motion.p>

              {/* Suggestion cards */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mt-10 w-full max-w-lg">
                {SUGGESTIONS.map((s, i) => (
                  <motion.button
                    key={s.title}
                    initial={{ opacity: 0, y: 16 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.4, delay: 0.35 + i * 0.08 }}
                    onClick={() => sendMessage({ text: s.message })}
                    className="group text-left rounded-xl border border-slate-200 bg-white p-4
                      hover:border-[#D4A853]/60 hover:shadow-md hover:shadow-[#D4A853]/5
                      transition-all duration-200 cursor-pointer"
                  >
                    <div className="flex items-start gap-3">
                      <div className="w-9 h-9 rounded-lg bg-[#0F172A]/[0.04] flex items-center justify-center shrink-0 group-hover:bg-[#D4A853]/10 transition-colors">
                        <s.icon className="w-[18px] h-[18px] text-[#0F172A]/60 group-hover:text-[#D4A853] transition-colors" />
                      </div>
                      <div className="min-w-0">
                        <p className="text-sm font-medium text-[#0F172A] leading-snug">{s.title}</p>
                        <p className="text-xs text-slate-400 mt-0.5 leading-relaxed">{s.description}</p>
                      </div>
                    </div>
                  </motion.button>
                ))}
              </div>

              {/* Subtle footer hint */}
              <motion.p
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ duration: 0.5, delay: 0.7 }}
                className="mt-8 text-xs text-slate-400"
              >
                Or type your question below to get started
              </motion.p>
            </div>
          )}

          {messages.map((message) => {
            // Check if this message has any visible content
            const visibleParts = message.parts.filter((part) => {
              if (part.type === "text") {
                const text = (part as any).text as string;
                // Hide META markers
                if (text.match(/^<<META:/)) return false;
                // Hide empty tool markers
                if (text.match(/^<<TOOL:\w+:\{[^>]*?\}>>$/) ) return true; // tools are visible
                // Hide empty/whitespace-only text
                const cleaned = text.replace(/<<META:[^>]+>>/g, "").replace(/<<TOOL:\w+:\{[^>]*?\}>>/g, "").trim();
                if (!cleaned && !text.match(/<<TOOL:/)) return false;
                return true;
              }
              if (part.type === "tool-invocation") return true;
              return false;
            });

            // Skip rendering entirely empty assistant bubbles
            if (message.role === "assistant" && visibleParts.length === 0) return null;

            return (
              <MessageBubble
                key={message.id}
                role={message.role as "user" | "assistant"}
                userImage={session?.user?.image}
                userName={session?.user?.name}
              >
                {message.parts.map((part, i) => {
                  const partType = part.type;

                  if (partType === "text") {
                    const text = (part as any).text as string;

                    // Hide META markers entirely
                    if (text.match(/^<<META:/)) return null;

                    // Hide raw JSON form submissions (tool payloads sent by the user)
                    if (message.role === "user" && text.trim().startsWith("{")) {
                      try {
                        const parsed = JSON.parse(text);
                        if (parsed.tool) {
                          return (
                            <p key={`${message.id}-${i}`} className="text-sm text-slate-400 italic">
                              {parsed.tool === "collect_basic_info" ? "Basic information submitted" :
                               parsed.tool === "collect_loan_details" ? "Loan details submitted" :
                               parsed.tool === "documents_submitted" ? `${Array.isArray(parsed.documents) ? parsed.documents.length : ""} documents submitted` :
                               "Form submitted"}
                            </p>
                          );
                        }
                      } catch { /* not JSON, render normally */ }
                    }

                    // Check for embedded tool markers: <<TOOL:tool_name:{...}>>
                    const toolMatch = text.match(/^<<TOOL:(\w+):([\s\S]+)>>$/);
                    if (toolMatch) {
                      try {
                        const toolData = JSON.parse(toolMatch[2]);
                        const toolName = toolData.__tool__ || toolMatch[1];
                        const { __tool__, ...args } = toolData;
                        return (
                          <ToolRenderer
                            key={`${message.id}-${i}`}
                            toolName={toolName}
                            data={args}
                            onSubmit={handleToolSubmit}
                          />
                        );
                      } catch {
                        // JSON parse failed — render as text
                      }
                    }

                    // Filter out tool/meta markers from mixed text content
                    const cleanText = text
                      .replace(/<<TOOL:\w+:\{[^>]*?\}>>/g, "")
                      .replace(/<<META:[^>]+>>/g, "")
                      .trim();
                    if (!cleanText) return null;

                    if (message.role === "assistant") {
                      return <MarkdownContent key={`${message.id}-${i}`} content={cleanText} />;
                    }
                    return (
                      <p
                        key={`${message.id}-${i}`}
                        className="whitespace-pre-wrap text-sm leading-relaxed"
                      >
                        {cleanText}
                      </p>
                    );
                  }

                  // Handle tool-invocation parts (standard Vercel AI SDK)
                  if (partType === "tool-invocation") {
                    const toolPart = part as any;
                    return (
                      <ToolRenderer
                        key={`${message.id}-${i}`}
                        toolName={toolPart.toolName}
                        data={toolPart.args || {}}
                        onSubmit={handleToolSubmit}
                      />
                    );
                  }

                  return null;
                })}
              </MessageBubble>
            );
          })}

          {isStreaming && (
            <MessageBubble role="assistant">
              <div className="flex items-center gap-2">
                <div className="flex gap-1">
                  <span className="w-2 h-2 bg-[#D4A853] rounded-full animate-bounce [animation-delay:0ms]" />
                  <span className="w-2 h-2 bg-[#D4A853] rounded-full animate-bounce [animation-delay:150ms]" />
                  <span className="w-2 h-2 bg-[#D4A853] rounded-full animate-bounce [animation-delay:300ms]" />
                </div>
                <span className="text-sm text-slate-400">Processing...</span>
              </div>
            </MessageBubble>
          )}
        </div>
      </div>

      <ChatInput
        onSend={(text) => sendMessage({ text })}
        disabled={isStreaming || toolQueue.length > 0 || uploadBatchActive}
      />
    </div>
  );
}
