"use client";

import { useState, useCallback } from "react";
import type { ChatMessage } from "@/lib/types";
import { queryDrug } from "@/lib/api";
import SMILESInput from "@/components/SMILESInput";
import ChatInterface from "@/components/ChatInterface";
import styles from "./page.module.css";

const RECENT_QUERIES = [
  { name: "Aspirin", smiles: "CC(=O)Oc1ccccc1C(=O)O" },
  { name: "Caffeine", smiles: "Cn1cnc2c1c(=O)n(c(=O)n2C)C" },
  { name: "Ibuprofen", smiles: "CC(C)Cc1ccc(cc1)C(C)C(=O)O" },
  { name: "Metformin", smiles: "CN(C)C(=N)NC(N)=N" },
  { name: "Paracetamol", smiles: "CC(=O)Nc1ccc(O)cc1" },
];

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
            <svg width="22" height="22" viewBox="0 0 22 22" fill="none">
              <circle cx="11" cy="11" r="4" stroke="var(--accent-primary)" strokeWidth="1.5" />
              <circle cx="3" cy="6" r="2.5" stroke="var(--accent-primary)" strokeWidth="1.2" strokeOpacity="0.6" />
              <circle cx="19" cy="6" r="2.5" stroke="var(--accent-primary)" strokeWidth="1.2" strokeOpacity="0.6" />
              <circle cx="3" cy="16" r="2.5" stroke="var(--accent-primary)" strokeWidth="1.2" strokeOpacity="0.6" />
              <circle cx="19" cy="16" r="2.5" stroke="var(--accent-primary)" strokeWidth="1.2" strokeOpacity="0.6" />
              <line x1="7" y1="9" x2="5.3" y2="7.5" stroke="var(--accent-primary)" strokeWidth="1.2" strokeOpacity="0.6" />
              <line x1="15" y1="9" x2="16.7" y2="7.5" stroke="var(--accent-primary)" strokeWidth="1.2" strokeOpacity="0.6" />
              <line x1="7" y1="13" x2="5.3" y2="14.5" stroke="var(--accent-primary)" strokeWidth="1.2" strokeOpacity="0.6" />
              <line x1="15" y1="13" x2="16.7" y2="14.5" stroke="var(--accent-primary)" strokeWidth="1.2" strokeOpacity="0.6" />
            </svg>
          </div>
          <div>
            <h1 className={styles.logoTitle}>PharmaRAG</h1>
            <p className={styles.logoSub}>Drug Information System</p>
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

          <div className={styles.navSection}>
            <span className={styles.navLabel}>Recent Queries</span>
            {RECENT_QUERIES.map((q) => (
              <button
                key={q.name}
                type="button"
                className={styles.historyItem}
                onClick={() => handleQuery(q.smiles)}
                disabled={loading}
              >
                <svg
                  className={styles.historyIcon}
                  width="14"
                  height="14"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="1.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
                </svg>
                <span>{q.name}</span>
              </button>
            ))}
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
