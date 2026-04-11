"use client";

import { useState, useRef, useEffect } from "react";
import { LinkedInProfile, ChatMessage, sendChatMessage } from "@/lib/api";

interface ChatPanelProps {
  profile: LinkedInProfile;
  userContext?: string;
  aiModel?: string;
  aiProvider?: string;
  aiApiKey?: string;
  aiBaseUrl?: string;
  onClose: () => void;
}

function buildProfileContext(profile: LinkedInProfile): string {
  const parts = [`Name: ${profile.name}`];
  if (profile.headline) parts.push(`Headline: ${profile.headline}`);
  if (profile.company) parts.push(`Company: ${profile.company}`);
  if (profile.role_title) parts.push(`Role: ${profile.role_title}`);
  if (profile.location) parts.push(`Location: ${profile.location}`);
  if (profile.field) parts.push(`Field: ${profile.field}`);
  if (profile.company_type) parts.push(`Company type: ${profile.company_type}`);
  if (profile.relevance_reason) parts.push(`AI assessment: ${profile.relevance_reason}`);
  if (profile.snippet) parts.push(`Profile info: ${profile.snippet}`);
  return parts.join("\n");
}

const QUICK_PROMPTS = [
  "Draft a LinkedIn connection request",
  "Draft a follow-up email after connecting",
  "What questions should I ask in an informational interview?",
  "Why is this person a good connection for me?",
];

export default function ChatPanel({ profile, userContext, aiModel, aiProvider, aiApiKey, aiBaseUrl, onClose }: ChatPanelProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const profileContext = buildProfileContext(profile);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const handleSend = async (text?: string) => {
    const content = text || input.trim();
    if (!content || isStreaming) return;

    const userMsg: ChatMessage = { role: "user", content };
    const newMessages = [...messages, userMsg];
    setMessages(newMessages);
    setInput("");
    setIsStreaming(true);

    const assistantMsg: ChatMessage = { role: "assistant", content: "" };
    setMessages([...newMessages, assistantMsg]);

    try {
      await sendChatMessage(newMessages, profileContext, userContext, aiModel, aiProvider, aiApiKey, aiBaseUrl, (partial) => {
        setMessages((prev) => {
          const updated = [...prev];
          updated[updated.length - 1] = { role: "assistant", content: partial };
          return updated;
        });
      });
    } catch (err) {
      setMessages((prev) => {
        const updated = [...prev];
        updated[updated.length - 1] = {
          role: "assistant",
          content: `Error: ${err instanceof Error ? err.message : "Chat failed"}`,
        };
        return updated;
      });
    } finally {
      setIsStreaming(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm">
      <div className="w-full max-w-2xl h-[80vh] bg-white rounded-2xl shadow-2xl flex flex-col overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-gray-200 bg-gradient-to-r from-indigo-50 to-purple-50">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-indigo-100 flex items-center justify-center text-indigo-700 font-bold text-sm">
              {profile.name
                .split(" ")
                .map((w) => w[0])
                .join("")
                .slice(0, 2)
                .toUpperCase()}
            </div>
            <div>
              <h3 className="font-semibold text-gray-900 text-sm">
                Chat about {profile.name}
              </h3>
              <p className="text-xs text-gray-500 truncate max-w-[300px]">
                {profile.headline || profile.role_title || "LinkedIn Profile"}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-200 rounded-lg transition-colors text-gray-500 hover:text-gray-700"
          >
            <svg width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
              <path d="M18 6L6 18M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-5 py-4 space-y-4">
          {messages.length === 0 && (
            <div className="text-center py-8">
              <div className="text-4xl mb-3">💬</div>
              <p className="text-gray-600 text-sm mb-5">
                Ask me to draft outreach messages, prepare interview questions, or discuss this profile.
              </p>
              <div className="flex flex-wrap justify-center gap-2">
                {QUICK_PROMPTS.map((prompt) => (
                  <button
                    key={prompt}
                    onClick={() => handleSend(prompt)}
                    className="px-3 py-2 text-xs bg-indigo-50 text-indigo-700 rounded-lg hover:bg-indigo-100 transition-colors border border-indigo-100"
                  >
                    {prompt}
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((msg, i) => (
            <div
              key={i}
              className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
            >
              <div
                className={`max-w-[85%] px-4 py-3 rounded-2xl text-sm leading-relaxed whitespace-pre-wrap ${
                  msg.role === "user"
                    ? "bg-indigo-600 text-white rounded-br-md"
                    : "bg-gray-100 text-gray-800 rounded-bl-md"
                }`}
              >
                {msg.content}
                {isStreaming && i === messages.length - 1 && msg.role === "assistant" && (
                  <span className="inline-block w-1.5 h-4 bg-indigo-500 ml-0.5 animate-pulse" />
                )}
              </div>
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div className="px-5 py-3 border-t border-gray-200 bg-gray-50">
          <div className="flex gap-2 items-end">
            <textarea
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Type a message... (Enter to send)"
              rows={1}
              className="flex-1 resize-none rounded-xl border border-gray-300 px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
              style={{ minHeight: "42px", maxHeight: "120px" }}
            />
            <button
              onClick={() => handleSend()}
              disabled={!input.trim() || isStreaming}
              className="px-4 py-2.5 bg-indigo-600 text-white rounded-xl hover:bg-indigo-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors text-sm font-medium"
            >
              Send
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
