"use client";

import { useState, useCallback } from "react";
import type { ChatMessage } from "@/lib/types";
import { queryDrug } from "@/lib/api";
import SMILESInput from "@/components/SMILESInput";
import ChatInterface from "@/components/ChatInterface";
import styles from "./page.module.css";


export default function HomePage() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(false);

  const handleQuery = useCallback(async (smiles: string) => {
    if (loading) return;

    const userMsg: ChatMessage = {
      id: `user-${Date.now()}`,
      role: "user",
      smiles,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMsg]);
    setLoading(true);

    try {
      const res = await queryDrug(smiles);

      const assistantMsg: ChatMessage = {
        id: `assistant-${Date.now()}`,
        role: "assistant",
        drugInfo: res.success ? res.data : undefined,
        error: res.success ? undefined : (res.error || "An unknown error occurred."),
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, assistantMsg]);
    } catch {
      const assistantMsg: ChatMessage = {
        id: `assistant-${Date.now()}`,
        role: "assistant",
        error: "Network error — could not reach the server.",
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } finally {
      setLoading(false);
    }
  }, [loading]);

  const handleNewChat = useCallback(() => {
    setMessages([]);
  }, []);

  return (
    <div className={styles.layout}>
      {/* ── Sidebar ── */}
      <aside className={styles.sidebar}>
        <div className={styles.logo}>
          <div className={styles.logoIcon} aria-hidden="true">
            <svg width="26" height="26" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <defs>
                <linearGradient id="pharmerPillTop" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" stopColor="#34d399" />
                  <stop offset="100%" stopColor="#059669" />
                </linearGradient>
                <linearGradient id="pharmerPillBottom" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" stopColor="#38bdf8" />
                  <stop offset="100%" stopColor="#0284c7" />
                </linearGradient>
              </defs>
              
              <g transform="rotate(-35 12 12)">
                <path d="M7 11.5V7A5 5 0 0 1 17 7V11.5H7Z" fill="url(#pharmerPillTop)" />
                <path d="M7 12.5V17A5 5 0 0 0 17 17V12.5H7Z" fill="url(#pharmerPillBottom)" />
                <rect x="6.5" y="11.25" width="11" height="1.5" fill="#0f131a" rx="0.75" />
              </g>
            </svg>
          </div>
          <div>
            <h1 className={styles.logoTitle}>Pharmer</h1>
            <p className={styles.logoSub}>Drug information retrieval</p>
          </div>
        </div>

        <nav className={styles.nav}>
          <div className={styles.newChatWrap}>
            <button
              type="button"
              className={styles.newChatBtn}
              onClick={handleNewChat}
              aria-label="Start new query thread"
            >
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                <path d="M8 3.5v9M3.5 8h9" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
              </svg>
              <span>New Query</span>
            </button>
          </div>


        </nav>

        <div className={styles.sidebarFooter}>
          <p>Educational use only</p>
          <p>Not clinical advice</p>
        </div>
      </aside>

      {/* ── Main content ── */}
      <main className={styles.main} id="main-content">
        {/* Top bar */}
        <div className={styles.topbar}>
          <h2 className={styles.topbarTitle}>Drug Query Assistant</h2>
        </div>

        {/* Input area */}
        <div className={styles.inputArea}>
          <SMILESInput onSubmit={handleQuery} loading={loading} />
        </div>

        {/* Chat thread */}
        <div className={styles.chatArea}>
          <ChatInterface messages={messages} loading={loading} />
        </div>
      </main>
    </div>
  );
}
