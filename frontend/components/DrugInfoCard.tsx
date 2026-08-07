"use client";

import { useState } from "react";
import type { DrugInfo, FieldValue } from "@/lib/types";
import StructureViewer from "./StructureViewer";
import CitationBadge from "./CitationBadge";
import styles from "./DrugInfoCard.module.css";

type Tab = "overview" | "pharmacodynamics" | "pharmacokinetics" | "safety" | "history";

interface Props {
  data: DrugInfo;
}

const TABS: { id: Tab; label: string; icon: string }[] = [
  { id: "overview",          label: "Overview",          icon: "🧬" },
  { id: "pharmacodynamics",  label: "Pharmacodynamics",  icon: "⚙️" },
  { id: "pharmacokinetics",  label: "Pharmacokinetics",  icon: "🔄" },
  { id: "safety",            label: "Safety",            icon: "🛡️" },
  { id: "history",           label: "History",           icon: "📖" },
];

// ── Sub-components ────────────────────────────────────────────────────────────

function SectionLabel({ children }: { children: React.ReactNode }) {
  return <h3 className={styles.sectionLabel}>{children}</h3>;
}

function InfoBlock({
  label,
  icon,
  field,
  accentColor = "teal",
}: {
  label: string;
  icon: string;
  field: FieldValue;
  accentColor?: "teal" | "indigo" | "amber" | "rose" | "violet";
}) {
  const [expanded, setExpanded] = useState(true);
  const isMissing = !field || field.missing || !field.content;
  const sources = field?.sources || [];

  return (
    <div
      className={`${styles.infoBlock} ${isMissing ? styles.infoBlockMissing : ""} ${styles[`accent-${accentColor}`]}`}
    >
      <button
        type="button"
        className={styles.infoBlockHeader}
        onClick={() => setExpanded((v) => !v)}
        aria-expanded={expanded}
        id={`field-${label.toLowerCase().replace(/\s+/g, "-")}`}
      >
        <span className={styles.infoBlockIcon}>{icon}</span>
        <span className={styles.infoBlockLabel}>{label}</span>
        <span className={styles.infoBlockRight}>
          {isMissing && (
            <span className={`badge badge-amber ${styles.missingBadge}`}>
              Data unavailable
            </span>
          )}
          <svg
            className={`${styles.chevron} ${expanded ? styles.chevronOpen : ""}`}
            width="16"
            height="16"
            viewBox="0 0 16 16"
            fill="none"
            aria-hidden="true"
          >
            <path
              d="M4 6l4 4 4-4"
              stroke="currentColor"
              strokeWidth="1.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        </span>
      </button>

      {expanded && (
        <div className={styles.infoBlockBody}>
          {isMissing ? (
            <p className={styles.missingText}>
              No data available from current sources. This field will be populated
              once relevant documents are ingested into the knowledge base.
            </p>
          ) : (
            <div className={styles.infoBlockContent}>
              {field.content!.split("\n").map((line, i) =>
                line.trim() ? (
                  <p key={i} className={styles.contentLine}>
                    {line}
                  </p>
                ) : (
                  <br key={i} />
                )
              )}
            </div>
          )}
          {sources.length > 0 && <CitationBadge citations={sources} />}
        </div>
      )}
    </div>
  );
}

function MetaChip({ label, value, mono = false }: { label: string; value: string; mono?: boolean }) {
  return (
    <div className={styles.metaChip}>
      <span className={styles.metaChipLabel}>{label}</span>
      <span className={`${styles.metaChipValue} ${mono ? styles.metaChipMono : ""}`}>{value}</span>
    </div>
  );
}

// ── Helpers ───────────────────────────────────────────────────────────────────

/** Returns a safe "data unavailable" FieldValue when data is missing/undefined. */
const MISSING: FieldValue = { content: null, sources: [], missing: true };

function safeField(f: FieldValue | undefined | null): FieldValue {
  return f ?? MISSING;
}

// ── Main card ─────────────────────────────────────────────────────────────────

export default function DrugInfoCard({ data }: Props) {
  const [activeTab, setActiveTab] = useState<Tab>("overview");

  const brandList = (data.drug_name.brand_names ?? []).join(", ");
  const labCodes  = (data.drug_name.lab_codes ?? []).join(", ");

  // Defensive normalization — handles old API responses missing new nested objects
  const pd   = data.pharmacodynamics   ?? {} as typeof data.pharmacodynamics;
  const tox  = data.toxicology         ?? {} as typeof data.toxicology;
  const tp   = data.therapeutic_profile ?? {} as typeof data.therapeutic_profile;
  const hist = data.history            ?? {} as typeof data.history;

  return (
    <div className={`${styles.card} animate-fade-in-up`}>

      {/* ── Header ── */}
      <div className={styles.header}>
        <div className={styles.headerLeft}>
          <div className={styles.drugIcon} aria-hidden="true">💊</div>
          <div>
            <h2 className={styles.genericName}>{data.drug_name.generic}</h2>
            {brandList && (
              <p className={styles.headerMeta}>
                <span className={styles.metaLabel}>Brand: </span>
                {brandList}
              </p>
            )}
            {labCodes && (
              <p className={styles.headerMeta}>
                <span className={styles.metaLabel}>Aliases: </span>
                {labCodes}
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
            <span className={styles.tabIcon}>{tab.icon}</span>
            {tab.label}
          </button>
        ))}
      </div>

      {/* ── Tab content ── */}
      <div className={styles.body}>

        {/* ── OVERVIEW ── */}
        {activeTab === "overview" && (
          <div className={styles.tabPanel} role="tabpanel" aria-labelledby="tab-overview">

            <section className={styles.section}>
              <SectionLabel>Drug Identity</SectionLabel>
              <div className={styles.metaGrid}>
                {data.chemical_structure.molecular_formula && (
                  <MetaChip label="Formula" value={data.chemical_structure.molecular_formula} mono />
                )}
                {data.chemical_structure.molecular_weight && (
                  <MetaChip label="Mol. Weight" value={`${data.chemical_structure.molecular_weight} g/mol`} mono />
                )}
                {data.chemical_structure.iupac_name && (
                  <MetaChip label="IUPAC Name" value={data.chemical_structure.iupac_name} />
                )}
                {data.chemical_structure.pubchem_cid && (
                  <MetaChip label="PubChem CID" value={String(data.chemical_structure.pubchem_cid)} mono />
                )}
              </div>
            </section>

            <div className={styles.divider} />

            <section className={styles.section}>
              <SectionLabel>Therapeutic Classes</SectionLabel>
              <InfoBlock
                label="Clinical & Pharmacological Classification"
                icon="🏷️"
                field={safeField(data.therapeutic_classes)}
                accentColor="indigo"
              />
            </section>

            <div className={styles.divider} />

            <section className={styles.section}>
              <SectionLabel>Molecular Structure</SectionLabel>
              <StructureViewer structure={data.chemical_structure} />
            </section>

          </div>
        )}

        {/* ── PHARMACODYNAMICS ── */}
        {activeTab === "pharmacodynamics" && (
          <div className={styles.tabPanel} role="tabpanel" aria-labelledby="tab-pharmacodynamics">
            <p className={styles.tabDescription}>
              How the drug interacts with biological targets at the molecular and cellular level.
            </p>

            <section className={styles.section}>
              <SectionLabel>Mechanism of Action</SectionLabel>
              <InfoBlock
                label="Mechanism of Action (Step-by-step)"
                icon="⚙️"
                field={safeField(pd.mechanism_of_action)}
                accentColor="teal"
              />
            </section>

            <div className={styles.divider} />

            <section className={styles.section}>
              <SectionLabel>Physiologic Effects</SectionLabel>
              <InfoBlock
                label="Physiologic Effect"
                icon="🫀"
                field={safeField(pd.physiologic_effect)}
                accentColor="teal"
              />
            </section>

            <div className={styles.divider} />

            <section className={styles.section}>
              <SectionLabel>Quantitative Parameters</SectionLabel>
              <div className={styles.pdGrid}>
                <InfoBlock
                  label="Binding Affinity (Kd / Ki)"
                  icon="🔗"
                  field={safeField(pd.binding_affinity)}
                  accentColor="violet"
                />
                <InfoBlock
                  label="Selectivity"
                  icon="🎯"
                  field={safeField(pd.selectivity)}
                  accentColor="violet"
                />
                <InfoBlock
                  label="Potency (EC₅₀ / ED₅₀)"
                  icon="📊"
                  field={safeField(pd.potency)}
                  accentColor="violet"
                />
                <InfoBlock
                  label="Efficacy (Emax)"
                  icon="📈"
                  field={safeField(pd.efficacy)}
                  accentColor="violet"
                />
              </div>
            </section>

          </div>
        )}

        {/* ── PHARMACOKINETICS ── */}
        {activeTab === "pharmacokinetics" && (
          <div className={styles.tabPanel} role="tabpanel" aria-labelledby="tab-pharmacokinetics">
            <p className={styles.tabDescription}>
              Pharmacokinetic profile — how the body absorbs, distributes, metabolizes, and excretes the drug.
            </p>

            <div className={styles.admeGrid}>
              <InfoBlock
                label="Absorption"
                icon="📥"
                field={data.adme.absorption}
                accentColor="teal"
              />
              <InfoBlock
                label="Distribution"
                icon="🌐"
                field={data.adme.distribution}
                accentColor="teal"
              />
              <InfoBlock
                label="Metabolism"
                icon="⚗️"
                field={data.adme.metabolism}
                accentColor="teal"
              />
              <InfoBlock
                label="Excretion"
                icon="📤"
                field={data.adme.excretion}
                accentColor="teal"
              />
            </div>

          </div>
        )}

        {/* ── SAFETY ── */}
        {activeTab === "safety" && (
          <div className={styles.tabPanel} role="tabpanel" aria-labelledby="tab-safety">

            <section className={styles.section}>
              <SectionLabel>Therapeutic Profile</SectionLabel>
              <InfoBlock
                label="Indications"
                icon="✅"
                field={safeField(tp.indications)}
                accentColor="teal"
              />
              <InfoBlock
                label="Contraindications"
                icon="🚫"
                field={safeField(tp.contraindications)}
                accentColor="rose"
              />
            </section>

            <div className={styles.divider} />

            <section className={styles.section}>
              <SectionLabel>Adverse Effects & Interactions</SectionLabel>
              <InfoBlock
                label="Adverse Effects"
                icon="⚠️"
                field={safeField(tp.adverse_effects)}
                accentColor="amber"
              />
              <InfoBlock
                label="Drug Interactions"
                icon="💊"
                field={safeField(tp.drug_interactions)}
                accentColor="amber"
              />
            </section>

            <div className={styles.divider} />

            <section className={styles.section}>
              <SectionLabel>Toxicology</SectionLabel>
              <div className={styles.toxGrid}>
                <InfoBlock
                  label="LD₅₀ (Animal Models)"
                  icon="🧪"
                  field={safeField(tox.ld50)}
                  accentColor="rose"
                />
                <InfoBlock
                  label="Toxic Doses (Human)"
                  icon="☠️"
                  field={safeField(tox.toxic_doses)}
                  accentColor="rose"
                />
                <InfoBlock
                  label="Organ Toxicity"
                  icon="🫁"
                  field={safeField(tox.organ_toxicity)}
                  accentColor="rose"
                />
                <InfoBlock
                  label="Overdose Management"
                  icon="🏥"
                  field={safeField(tox.overdose_management)}
                  accentColor="indigo"
                />
              </div>
            </section>

          </div>
        )}

        {/* ── HISTORY ── */}
        {activeTab === "history" && (
          <div className={styles.tabPanel} role="tabpanel" aria-labelledby="tab-history">
            <p className={styles.tabDescription}>
              The scientific and clinical journey from discovery to modern use.
            </p>

            <div className={styles.historyTimeline}>
              <div className={styles.historyStep}>
                <div className={styles.historyStepMarker}>
                  <span className={styles.historyStepIcon}>🔬</span>
                  <div className={styles.historyStepLine} />
                </div>
                <div className={styles.historyStepContent}>
                  <SectionLabel>Background</SectionLabel>
                  <InfoBlock
                    label="Medical Context & Unmet Need"
                    icon="📜"
                    field={safeField(hist.background)}
                    accentColor="indigo"
                  />
                </div>
              </div>

              <div className={styles.historyStep}>
                <div className={styles.historyStepMarker}>
                  <span className={styles.historyStepIcon}>💡</span>
                  <div className={styles.historyStepLine} />
                </div>
                <div className={styles.historyStepContent}>
                  <SectionLabel>Discovery</SectionLabel>
                  <InfoBlock
                    label="Lead Compound Origin"
                    icon="🌿"
                    field={safeField(hist.discovery)}
                    accentColor="indigo"
                  />
                </div>
              </div>

              <div className={styles.historyStep}>
                <div className={styles.historyStepMarker}>
                  <span className={styles.historyStepIcon}>⚗️</span>
                  <div className={styles.historyStepLine} />
                </div>
                <div className={styles.historyStepContent}>
                  <SectionLabel>Development</SectionLabel>
                  <InfoBlock
                    label="Optimization, Preclinical & Patents"
                    icon="🏭"
                    field={safeField(hist.development)}
                    accentColor="indigo"
                  />
                </div>
              </div>

              <div className={styles.historyStep}>
                <div className={styles.historyStepMarker}>
                  <span className={styles.historyStepIcon}>🏥</span>
                </div>
                <div className={styles.historyStepContent}>
                  <SectionLabel>Clinical Trials</SectionLabel>
                  <InfoBlock
                    label="Phase I–III & Regulatory Approvals"
                    icon="📋"
                    field={safeField(hist.clinical_trials)}
                    accentColor="indigo"
                  />
                </div>
              </div>
            </div>

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
        <span className="badge badge-teal">PharmaRAG</span>
      </div>
    </div>
  );
}
