"use client";

import React, { useState, useRef, useEffect } from "react";
import {
  Send,
  MessageSquare,
  Sparkles,
  BookOpen,
  User,
  Bot,
  Loader2,
  X,
  Globe,
  ExternalLink,
} from "lucide-react";
import { ChatMessage, Citation, sendChatMessage, sendWebSearchQuery } from "@/lib/api";
import { MarkdownRenderer } from "@/components/MarkdownRenderer";

interface GroundedChatProps {
  documentIds: string[];
  documentTitle: string;
}

export const GroundedChat: React.FC<GroundedChatProps> = ({ documentIds, documentTitle }) => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputMsg, setInputMsg] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [isSearchingWeb, setIsSearchingWeb] = useState(false);
  const [activeCitation, setActiveCitation] = useState<Citation | null>(null);
  const [sessionId, setSessionId] = useState<string | undefined>(undefined);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isSending]);

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputMsg.trim() || isSending) return;

    const userText = inputMsg.trim();
    setInputMsg("");

    const tempUserMsg: ChatMessage = {
      session_id: sessionId || "temp",
      message_id: Date.now().toString(),
      sender: "user",
      content: userText,
      citations: [],
      created_at: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, tempUserMsg]);
    setIsSending(true);

    try {
      const responseMsg = await sendChatMessage(documentIds, userText, sessionId);
      if (!sessionId) {
        setSessionId(responseMsg.session_id);
      }
      setMessages((prev) => [...prev, responseMsg]);
    } catch (err: unknown) {
      const errorAsstMsg: ChatMessage = {
        session_id: sessionId || "temp",
        message_id: Date.now().toString(),
        sender: "assistant",
        content:
          "Sorry, I encountered an error processing your document question. Please try again.",
        citations: [],
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, errorAsstMsg]);
    } finally {
      setIsSending(false);
    }
  };

  const handleWebSearch = async (queryText: string, msgId: string) => {
    if (isSending) return;

    // Dismiss buttons on the prompt message
    setMessages((prev) =>
      prev.map((m) => (m.message_id === msgId ? { ...m, offer_web_search: false } : m))
    );

    setIsSending(true);
    setIsSearchingWeb(true);

    try {
      const responseMsg = await sendWebSearchQuery(documentIds, queryText, sessionId);
      if (!sessionId) {
        setSessionId(responseMsg.session_id);
      }
      setMessages((prev) => [...prev, responseMsg]);
    } catch (err: unknown) {
      const errorMsg: ChatMessage = {
        session_id: sessionId || "temp",
        message_id: Date.now().toString(),
        sender: "assistant",
        content: "Web search didn't return results for this or encountered a network error.",
        citations: [],
        is_web_result: true,
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsSending(false);
      setIsSearchingWeb(false);
    }
  };

  const handleDeclineWebSearch = (msgId: string) => {
    setMessages((prev) =>
      prev.map((m) => (m.message_id === msgId ? { ...m, offer_web_search: false } : m))
    );
  };

  return (
    <div className="glass-panel rounded-2xl border border-slate-200 dark:border-slate-800 flex flex-col h-[750px] overflow-hidden sticky top-24 shadow-2xl transition-colors">
      {/* Chat Header */}
      <div className="p-4 border-b border-slate-200/80 dark:border-slate-800/80 bg-slate-100/90 dark:bg-slate-900/90 flex items-center justify-between transition-colors">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-indigo-600 via-cyan-500 to-emerald-500 p-0.5 shadow-md">
            <div className="w-full h-full bg-white dark:bg-slate-950 rounded-[10px] flex items-center justify-center text-indigo-600 dark:text-indigo-400">
              <MessageSquare className="w-4 h-4" />
            </div>
          </div>
          <div>
            <h3 className="text-sm font-semibold text-slate-900 dark:text-white flex items-center gap-1.5">
              Smart Document Assistant
            </h3>
            <p className="text-[11px] text-slate-500 dark:text-slate-400 truncate max-w-[200px]">
              {documentTitle}
            </p>
          </div>
        </div>
        <span className="px-2.5 py-1 text-[10px] font-semibold bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 rounded-full border border-emerald-500/20">
          Document-Only Mode
        </span>
      </div>

      {/* Messages List */}
      <div className="flex-1 p-4 overflow-y-auto space-y-4">
        {messages.length === 0 ? (
          <div className="text-center py-16 space-y-3">
            <div className="w-12 h-12 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center mx-auto text-indigo-500 dark:text-indigo-400 shadow-inner">
              <Sparkles className="w-6 h-6" />
            </div>
            <p className="text-sm font-medium text-slate-800 dark:text-slate-200">
              Ask document questions
            </p>
            <p className="text-xs text-slate-500 dark:text-slate-400 max-w-xs mx-auto">
              Ask about experience, metrics, key terms, or risks. Every answer cites source pages,
              with opt-in live web search fallback.
            </p>
          </div>
        ) : (
          messages.map((msg) => (
            <div
              key={msg.message_id}
              className={`flex flex-col ${msg.sender === "user" ? "items-end" : "items-start"}`}
            >
              <div
                className={`max-w-[94%] p-4 sm:p-5 rounded-2xl text-xs leading-relaxed space-y-3 shadow-xl ${
                  msg.sender === "user"
                    ? "bg-gradient-to-r from-indigo-600 to-indigo-700 text-white rounded-tr-none font-medium border border-indigo-500/30"
                    : msg.is_web_result
                      ? "bg-slate-100 dark:bg-slate-900/95 border border-cyan-500/30 text-slate-800 dark:text-slate-200 rounded-tl-none shadow-cyan-950/20"
                      : "bg-slate-100 dark:bg-slate-900/95 border border-slate-200 dark:border-slate-800/90 text-slate-800 dark:text-slate-200 rounded-tl-none"
                }`}
              >
                {msg.sender === "assistant" && (
                  <div className="flex items-center justify-between pb-2.5 border-b border-slate-200/80 dark:border-slate-800/80">
                    <span className="flex items-center gap-1.5 text-[11px] font-semibold text-indigo-600 dark:text-indigo-400">
                      {msg.is_web_result ? (
                        <>
                          <Globe className="w-3.5 h-3.5 text-cyan-600 dark:text-cyan-400" />
                          <span className="text-cyan-600 dark:text-cyan-400">Live Web Search</span>
                        </>
                      ) : (
                        <>
                          <Bot className="w-3.5 h-3.5" />
                          Document-Based Answer
                        </>
                      )}
                    </span>

                    {msg.is_web_result ? (
                      <span className="flex items-center gap-1.5 text-[10px] text-cyan-700 dark:text-cyan-300 bg-cyan-500/10 px-2.5 py-0.5 rounded-full border border-cyan-500/30 font-semibold shadow-sm">
                        <span className="w-1.5 h-1.5 rounded-full bg-cyan-500 dark:bg-cyan-400 animate-pulse" />
                        Web Result — Live Search
                      </span>
                    ) : (
                      <span className="flex items-center gap-1 text-[10px] text-emerald-600 dark:text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-full border border-emerald-500/20 font-medium">
                        <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 dark:bg-emerald-400 animate-pulse" />
                        Verified from Document
                        <span
                          className="ml-0.5 w-3.5 h-3.5 rounded-full bg-emerald-500/20 text-emerald-700 dark:text-emerald-300 flex items-center justify-center text-[9px] font-bold cursor-help"
                          title="This answer uses only information found in your uploaded document."
                        >
                          ?
                        </span>
                      </span>
                    )}
                  </div>
                )}

                {msg.sender === "user" ? (
                  <p className="text-xs sm:text-sm">{msg.content}</p>
                ) : (
                  <MarkdownRenderer
                    content={msg.content}
                    citations={msg.citations}
                    onCitationClick={(tag) => {
                      const match = msg.citations.find(
                        (c) => c.chunk_id.includes(tag) || tag.includes(c.chunk_id)
                      );
                      if (match) setActiveCitation(match);
                    }}
                  />
                )}

                {/* Opt-In Web Search Action Buttons */}
                {msg.sender === "assistant" && msg.offer_web_search && (
                  <div className="mt-3 pt-3 border-t border-slate-200/80 dark:border-slate-800/80 space-y-2">
                    <p className="text-[11px] font-semibold text-slate-700 dark:text-slate-300">
                      Would you like to search external web sources for this?
                    </p>
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() =>
                          handleWebSearch(msg.original_query || msg.content, msg.message_id)
                        }
                        disabled={isSending}
                        className="px-3.5 py-2 rounded-xl bg-gradient-to-r from-cyan-600 to-indigo-600 hover:from-cyan-500 hover:to-indigo-500 text-white font-medium text-xs shadow-lg shadow-cyan-900/30 transition-all flex items-center gap-1.5 active:scale-95 disabled:opacity-50 cursor-pointer"
                      >
                        <Globe className="w-3.5 h-3.5 text-cyan-200" />
                        Yes, search the web
                      </button>
                      <button
                        onClick={() => handleDeclineWebSearch(msg.message_id)}
                        disabled={isSending}
                        className="px-3 py-2 rounded-xl bg-slate-200 dark:bg-slate-800 hover:bg-slate-300 dark:hover:bg-slate-700 text-slate-800 dark:text-slate-300 text-xs font-medium border border-slate-300 dark:border-slate-700 transition-all active:scale-95 disabled:opacity-50 cursor-pointer"
                      >
                        No, just document
                      </button>
                    </div>
                  </div>
                )}

                {/* Citations Footer Badges (Document Chunks) */}
                {msg.citations && msg.citations.length > 0 && msg.sender === "assistant" && (
                  <div className="pt-3 border-t border-slate-200/80 dark:border-slate-800/80 flex flex-wrap items-center gap-1.5">
                    <span className="text-[10px] font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                      Source References:
                    </span>
                    {msg.citations.map((cit, idx) => (
                      <button
                        key={idx}
                        onClick={() => setActiveCitation(cit)}
                        data-chunk-id={cit.chunk_id}
                        title={`Source Chunk ID: ${cit.chunk_id}`}
                        className="px-2 py-0.5 rounded bg-indigo-500/10 dark:bg-indigo-500/20 hover:bg-indigo-500/30 text-indigo-700 dark:text-indigo-300 text-[10px] font-medium border border-indigo-500/30 transition-all flex items-center gap-1 active:scale-95 cursor-pointer"
                      >
                        <BookOpen className="w-3 h-3 text-indigo-600 dark:text-indigo-400" />
                        Page {cit.page_number || 1}
                      </button>
                    ))}
                  </div>
                )}

                {/* Live Web Citations Footer Badges */}
                {msg.is_web_result && msg.web_citations && msg.web_citations.length > 0 && (
                  <div className="pt-3 border-t border-slate-200/80 dark:border-slate-800/80 flex flex-col gap-1.5">
                    <span className="text-[10px] font-semibold text-cyan-600 dark:text-cyan-400 uppercase tracking-wider flex items-center gap-1">
                      <Globe className="w-3 h-3 text-cyan-600 dark:text-cyan-400" />
                      Live Web Citations:
                    </span>
                    <div className="flex flex-wrap gap-2">
                      {msg.web_citations.map((cit, idx) => (
                        <a
                          key={idx}
                          href={cit.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="px-2.5 py-1 rounded bg-cyan-50 dark:bg-cyan-950/80 hover:bg-cyan-100 dark:hover:bg-cyan-900/80 text-cyan-700 dark:text-cyan-300 text-[11px] border border-cyan-200 dark:border-cyan-800/60 transition-all flex items-center gap-1.5 font-medium group"
                        >
                          <span className="truncate max-w-[200px]">{cit.title || cit.url}</span>
                          <ExternalLink className="w-3 h-3 text-cyan-600 dark:text-cyan-400 group-hover:scale-110 transition-transform" />
                        </a>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          ))
        )}

        {isSending && (
          <div className="flex items-center gap-3 p-4 rounded-2xl bg-slate-100 dark:bg-slate-900/90 border border-cyan-500/40 shadow-xl max-w-[88%] animate-pulse">
            <div className="w-8 h-8 rounded-xl bg-cyan-500/20 border border-cyan-500/30 flex items-center justify-center text-cyan-500 dark:text-cyan-400 flex-shrink-0">
              <Loader2 className="w-4 h-4 animate-spin text-cyan-500 dark:text-cyan-400" />
            </div>
            <div className="space-y-0.5">
              <div className="flex items-center gap-2">
                <p className="text-xs font-semibold text-slate-900 dark:text-white">
                  {isSearchingWeb
                    ? "Searching Live Web & Synthesizing..."
                    : "Searching document & drafting response..."}
                </p>
                <span className="w-2 h-2 rounded-full bg-cyan-400 animate-ping" />
              </div>
              <p className="text-[11px] text-slate-500 dark:text-slate-400">
                {isSearchingWeb
                  ? "Querying external web sources & building cited response..."
                  : "Reading document pages & synthesizing answer..."}
              </p>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Citation Preview Drawer */}
      {activeCitation && (
        <div className="p-3 bg-slate-100 dark:bg-slate-900 border-t border-indigo-500/30 text-xs space-y-1.5 shadow-2xl animate-in slide-in-from-bottom-2">
          <div className="flex items-center justify-between text-indigo-600 dark:text-indigo-400 font-mono text-[11px]">
            <span
              className="flex items-center gap-1 font-semibold"
              title={`Source Chunk ID: ${activeCitation.chunk_id}`}
            >
              <BookOpen className="w-3.5 h-3.5" />
              Source Excerpt: Page {activeCitation.page_number || 1}
            </span>
            <button
              onClick={() => setActiveCitation(null)}
              className="text-slate-400 hover:text-slate-900 dark:hover:text-white p-1"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
          <p className="text-slate-700 dark:text-slate-300 italic bg-white dark:bg-slate-950 p-2.5 rounded-lg border border-slate-200 dark:border-slate-800 text-[11px] leading-relaxed">
            "{activeCitation.snippet}"
          </p>
        </div>
      )}

      {/* Chat Input Form */}
      <form
        onSubmit={handleSend}
        className="p-3 border-t border-slate-200/80 dark:border-slate-800/80 bg-slate-100/80 dark:bg-slate-900/80 flex items-center gap-2 transition-colors"
      >
        <input
          type="text"
          value={inputMsg}
          disabled={isSending}
          onChange={(e) => setInputMsg(e.target.value)}
          placeholder={
            isSending
              ? isSearchingWeb
                ? "Searching web for answer..."
                : "AI is synthesizing response..."
              : "Ask a question about the document..."
          }
          className="flex-1 bg-white dark:bg-slate-950 border border-slate-300 dark:border-slate-800 focus:border-indigo-500 rounded-xl px-4 py-2.5 text-xs text-slate-900 dark:text-white placeholder-slate-400 dark:placeholder-slate-500 outline-none transition-colors disabled:opacity-60"
        />
        <button
          type="submit"
          disabled={!inputMsg.trim() || isSending}
          className="p-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white transition-all shadow-md shadow-indigo-600/30 flex items-center justify-center cursor-pointer"
        >
          {isSending ? (
            <Loader2 className="w-4 h-4 animate-spin text-white" />
          ) : (
            <Send className="w-4 h-4" />
          )}
        </button>
      </form>
    </div>
  );
};
