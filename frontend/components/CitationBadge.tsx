"use client";

import type { Citation } from "@/lib/types";
import styles from "./CitationBadge.module.css";

interface Props {
  citations: Citation[];
}

export default function CitationBadge({ citations }: Props) {
  if (!citations || citations.length === 0) return null;

  return (
    <div className={styles.citations}>
      {citations.map((c, i) => (
        <a
          key={i}
          href={c.url || "#"}
          target={c.url ? "_blank" : undefined}
          rel="noopener noreferrer"
          className={styles.badge}
          title={c.source}
        >
          <svg width="10" height="10" viewBox="0 0 10 10" fill="none" aria-hidden="true">
            <circle cx="5" cy="5" r="4" stroke="currentColor" strokeWidth="1.2" />
            <text x="5" y="7.5" textAnchor="middle" fontSize="6" fill="currentColor" fontWeight="600">i</text>
          </svg>
          {c.source}
        </a>
      ))}
    </div>
  );
}
