"use client";

import { useRef, useEffect } from "react";
import type { ChatMessage } from "@/lib/types";
import DrugInfoCard from "./DrugInfoCard";
import styles from "./ChatInterface.module.css";

interface Props {
  messages: ChatMessage[];
  loading: boolean;
}

export default function ChatInterface({ messages, loading }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  if (messages.length === 0 && !loading) {
    return (
      <div className={styles.empty}>
        <div className={styles.emptyIcon} aria-hidden="true">
          <svg width="48" height="48" viewBox="0 0 48 48" fill="none">
            <circle cx="24" cy="24" r="8" stroke="var(--accent-primary)" strokeWidth="1.5" />
            <circle cx="8" cy="16" r="4" stroke="var(--accent-primary)" strokeWidth="1.5" strokeOpacity="0.5" />
            <circle cx="40" cy="16" r="4" stroke="var(--accent-primary)" strokeWidth="1.5" strokeOpacity="0.5" />
            <circle cx="8" cy="32" r="4" stroke="var(--accent-primary)" strokeWidth="1.5" strokeOpacity="0.5" />
            <circle cx="40" cy="32" r="4" stroke="var(--accent-primary)" strokeWidth="1.5" strokeOpacity="0.5" />
            <line x1="16" y1="20" x2="12" y2="18" stroke="var(--accent-primary)" strokeWidth="1.5" strokeOpacity="0.5" />
            <line x1="32" y1="20" x2="36" y2="18" stroke="var(--accent-primary)" strokeWidth="1.5" strokeOpacity="0.5" />
            <line x1="16" y1="28" x2="12" y2="30" stroke="var(--accent-primary)" strokeWidth="1.5" strokeOpacity="0.5" />
            <line x1="32" y1="28" x2="36" y2="30" stroke="var(--accent-primary)" strokeWidth="1.5" strokeOpacity="0.5" />
          </svg>
        </div>
        <h2 className={styles.emptyTitle}>Enter a SMILES string to begin</h2>
        <p className={styles.emptyDesc}>
          Submit any valid SMILES notation to retrieve a detailed pharmacological
          breakdown — Overview, Pharmacodynamics, Pharmacokinetics (ADME),
          Safety &amp; Toxicology, and Drug History.
        </p>
        <div className={styles.emptyHints}>
          <span className={styles.hint}>
            <span className={styles.hintDot} />
            All fields are grounded in cited sources
          </span>
          <span className={styles.hint}>
            <span className={styles.hintDot} />
            Missing data is flagged, never fabricated
          </span>
          <span className={styles.hint}>
            <span className={styles.hintDot} />
            Educational use only — not clinical advice
          </span>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.thread}>
      {messages.map((msg) => (
        <div key={msg.id} className={styles.message}>
          {msg.role === "user" && (
            <div className={styles.userBubble}>
              <div className={styles.userAvatar} aria-label="You">You</div>
              <div className={styles.userContent}>
                <span className={styles.userLabel}>SMILES query</span>
                <code className={styles.userSmiles}>{msg.smiles}</code>
              </div>
            </div>
          )}

          {msg.role === "assistant" && msg.drugInfo && (
            <div className={styles.assistantBubble}>
              <div className={styles.assistantAvatar} aria-label="PharmaRAG">
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                  <circle cx="8" cy="8" r="3" fill="var(--accent-primary)" />
                  <circle cx="2" cy="4" r="1.5" fill="var(--accent-primary)" fillOpacity="0.5" />
                  <circle cx="14" cy="4" r="1.5" fill="var(--accent-primary)" fillOpacity="0.5" />
                  <circle cx="2" cy="12" r="1.5" fill="var(--accent-primary)" fillOpacity="0.5" />
                  <circle cx="14" cy="12" r="1.5" fill="var(--accent-primary)" fillOpacity="0.5" />
                </svg>
              </div>
              <div className={styles.assistantContent}>
                <DrugInfoCard data={msg.drugInfo} />
              </div>
            </div>
          )}

          {msg.role === "assistant" && msg.error && (
            <div className={styles.errorBubble}>
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
                <circle cx="8" cy="8" r="7" stroke="var(--color-error)" strokeWidth="1.2" />
                <path d="M8 4v5M8 11v1" stroke="var(--color-error)" strokeWidth="1.2" strokeLinecap="round" />
              </svg>
              {msg.error}
            </div>
          )}
        </div>
      ))}

      {loading && (
        <div className={styles.loadingBubble}>
          <div className={styles.assistantAvatar} aria-hidden="true">
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
              <circle cx="8" cy="8" r="3" fill="var(--accent-primary)" />
              <circle cx="2" cy="4" r="1.5" fill="var(--accent-primary)" fillOpacity="0.5" />
              <circle cx="14" cy="4" r="1.5" fill="var(--accent-primary)" fillOpacity="0.5" />
            </svg>
          </div>
          <div className={styles.loadingContent}>
            <div className={styles.loadingDots}>
              <span /><span /><span />
            </div>
            <span className={styles.loadingText}>Retrieving drug information…</span>
          </div>
        </div>
      )}

      <div ref={bottomRef} />
    </div>
  );
}
