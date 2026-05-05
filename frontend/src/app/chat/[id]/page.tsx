"use client";

import { useParams } from "next/navigation";
import { ChatInterface } from "@/components/chat/chat-interface";

export default function ChatConversationPage() {
  const { id } = useParams();
  return <ChatInterface conversationId={id as string} />;
}
