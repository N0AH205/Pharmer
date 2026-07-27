"use client";

import { useState } from "react";
import type { DrugInfo } from "@/lib/types";
import FieldBlock from "./FieldBlock";
import StructureViewer from "./StructureViewer";
import CitationBadge from "./CitationBadge";
import styles from "./DrugInfoCard.module.css";

type Tab = "overview" | "adme" | "safety" | "interactions";

interface Props {
  data: DrugInfo;
}

const TABS: { id: Tab; label: string }[] = [
  { id: "overview", label: "Overview" },
  { id: "adme", label: "ADME" },
  { id: "safety", label: "Safety" },
  { id: "interactions", label: "Interactions" },
];

export default function DrugInfoCard({ data }: Props) {
  const [activeTab, setActiveTab] = useState<Tab>("overview");

  const brandList = data.drug_name.brand_names.join(", ");

  return (
    <div className={`${styles.card} animate-fade-in-up`}>
      {/* ── Header ── */}
      <div className={styles.header}>
        <div className={styles.headerLeft}>
          <div className={styles.drugIcon} aria-hidden="true">💊</div>
          <div>
            <h2 className={styles.genericName}>{data.drug_name.generic}</h2>
            {brandList && (
              <p className={styles.brandNames}>
                <span className={styles.brandLabel}>Brand: </span>
                {brandList}
              </p>
            )}
          </div>
        </div>
        <div className={styles.headerRight}>
          <div className={styles.smilesChip}>
            <span className={styles.smilesChipLabel}>SMILES</span>
            <code className={styles.smilesCode}>{data.query_smiles}</code>
          </div>
          <CitationBadge citations={data.drug_name.sources} />
        </div>
      </div>

      {/* ── Tabs ── */}
      <div className={styles.tabs} role="tablist">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            role="tab"
            aria-selected={activeTab === tab.id}
            id={`tab-${tab.id}`}
            className={`${styles.tab} ${activeTab === tab.id ? styles.tabActive : ""}`}
            onClick={() => setActiveTab(tab.id)}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* ── Tab content ── */}
      <div className={styles.body}>
        {activeTab === "overview" && (
          <div className={styles.tabPanel} role="tabpanel" aria-labelledby="tab-overview">
            <section className={styles.section}>
              <h3 className={styles.sectionTitle}>Chemical Structure</h3>
              <StructureViewer structure={data.chemical_structure} />
            </section>

            <div className={styles.divider} />

            <section className={styles.section}>
              <h3 className={styles.sectionTitle}>Mechanism of Action</h3>
              <FieldBlock
                label="Mechanism of Action"
                icon="⚙️"
                field={data.mechanism_of_action}
                defaultExpanded
              />
            </section>

            <div className={styles.divider} />

            <section className={styles.section}>
              <h3 className={styles.sectionTitle}>Indications</h3>
              <FieldBlock
                label="Approved Indications"
                icon="✅"
                field={data.indications}
                defaultExpanded
              />
            </section>
          </div>
        )}

        {activeTab === "adme" && (
          <div className={styles.tabPanel} role="tabpanel" aria-labelledby="tab-adme">
            <p className={styles.sectionSubtitle}>
              Pharmacokinetic profile — Absorption, Distribution, Metabolism, Excretion
            </p>
            <div className={styles.admeGrid}>
              <FieldBlock label="Absorption" icon="📥" field={data.adme.absorption} defaultExpanded />
              <FieldBlock label="Distribution" icon="🔄" field={data.adme.distribution} defaultExpanded />
              <FieldBlock label="Metabolism" icon="⚗️" field={data.adme.metabolism} defaultExpanded />
              <FieldBlock label="Excretion" icon="📤" field={data.adme.excretion} defaultExpanded />
            </div>
          </div>
        )}

        {activeTab === "safety" && (
          <div className={styles.tabPanel} role="tabpanel" aria-labelledby="tab-safety">
            <div className={styles.safetyFields}>
              <FieldBlock
                label="Contraindications"
                icon="🚫"
                field={data.contraindications}
                defaultExpanded
              />
              <FieldBlock
                label="Adverse Effects"
                icon="⚠️"
                field={data.adverse_effects}
                defaultExpanded
              />
            </div>
          </div>
        )}

        {activeTab === "interactions" && (
          <div className={styles.tabPanel} role="tabpanel" aria-labelledby="tab-interactions">
            <FieldBlock
              label="Drug Interactions"
              icon="🔗"
              field={data.drug_interactions}
              defaultExpanded
            />
          </div>
        )}
      </div>

      {/* ── Disclaimer ── */}
      <div className={styles.disclaimer}>
        <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true">
          <circle cx="7" cy="7" r="6" stroke="currentColor" strokeWidth="1.2" />
          <path d="M7 4v4M7 9.5v.5" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" />
        </svg>
        {data.disclaimer}
      </div>

      {/* ── Footer ── */}
      <div className={styles.footer}>
        <span className={styles.footerText}>
          Generated {new Date(data.generated_at).toLocaleString()}
        </span>
        <span className="badge badge-teal">Phase 1 — Mock Data</span>
      </div>
    </div>
  );
}
