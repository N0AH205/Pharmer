"use client";

import { useState } from "react";
import type { FieldValue } from "@/lib/types";
import CitationBadge from "./CitationBadge";
import styles from "./FieldBlock.module.css";

interface Props {
  label: string;
  icon?: string;
  field?: FieldValue;
  defaultExpanded?: boolean;
}

export default function FieldBlock({ label, icon, field, defaultExpanded = false }: Props) {
  const [expanded, setExpanded] = useState(defaultExpanded);

  const isMissing = !field || field.missing || !field.content;
  const sources = field?.sources || [];

  return (
    <div className={`${styles.block} ${isMissing ? styles.missing : ""}`}>
      <button
        type="button"
        className={styles.header}
        onClick={() => setExpanded((v) => !v)}
        aria-expanded={expanded}
        id={`field-${label.toLowerCase().replace(/\s+/g, "-")}`}
      >
        <span className={styles.iconLabel}>
          {icon && <span className={styles.icon}>{icon}</span>}
          <span className={styles.label}>{label}</span>
        </span>
        <span className={styles.right}>
          {isMissing && (
            <span className="badge badge-amber">Data unavailable</span>
          )}
          <svg
            className={`${styles.chevron} ${expanded ? styles.chevronOpen : ""}`}
            width="16"
            height="16"
            viewBox="0 0 16 16"
            fill="none"
            aria-hidden="true"
          >
            <path d="M4 6l4 4 4-4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </span>
      </button>

      {expanded && (
        <div className={styles.body}>
          {isMissing ? (
            <p className={styles.missingText}>
              No data available from current sources. This field will be populated
              once relevant documents are ingested into the knowledge base.
            </p>
          ) : (
            <div className={styles.content}>
              {field.content!.split("\n").map((line, i) =>
                line.trim() ? (
                  <p key={i} className={styles.line}>
                    {line}
                  </p>
                ) : (
                  <br key={i} />
                )
              )}
            </div>
          )}
          <CitationBadge citations={sources} />
        </div>
      )}
    </div>
  );
}
