"use client";

import { useState } from "react";
import type { ChemicalStructure } from "@/lib/types";
import CitationBadge from "./CitationBadge";
import styles from "./StructureViewer.module.css";

interface Props {
  structure: ChemicalStructure;
}

export default function StructureViewer({ structure }: Props) {
  const [imgError, setImgError] = useState(false);

  return (
    <div className={styles.container}>
      <div className={styles.imageWrap}>
        {structure.image_url && !imgError ? (
          /* eslint-disable-next-line @next/next/no-img-element */
          <img
            src={structure.image_url}
            alt={`Chemical structure of ${structure.iupac_name || structure.smiles}`}
            className={styles.image}
            onError={() => setImgError(true)}
          />
        ) : (
          <div className={styles.imageFallback}>
            <span>Structure image unavailable</span>
          </div>
        )}
      </div>

      <div className={styles.properties}>
        <div className={styles.propGrid}>
          {structure.iupac_name && (
            <Prop label="IUPAC name" value={structure.iupac_name} mono={false} />
          )}
          {structure.molecular_formula && (
            <Prop label="Formula" value={structure.molecular_formula} mono />
          )}
          {structure.molecular_weight && (
            <Prop label="Mol. weight" value={`${structure.molecular_weight} g/mol`} mono />
          )}
          {structure.pubchem_cid && (
            <Prop
              label="PubChem CID"
              value={String(structure.pubchem_cid)}
              mono
              link={`https://pubchem.ncbi.nlm.nih.gov/compound/${structure.pubchem_cid}`}
            />
          )}
        </div>

        <div className={styles.smilesRow}>
          <span className={styles.smilesLabel}>SMILES</span>
          <code className={styles.smiles}>{structure.smiles}</code>
        </div>

        {structure.inchi && (
          <div className={styles.smilesRow}>
            <span className={styles.smilesLabel}>InChI</span>
            <code className={`${styles.smiles} ${styles.smilesMuted}`}>
              {structure.inchi}
            </code>
          </div>
        )}

        <CitationBadge citations={structure.sources} />
      </div>
    </div>
  );
}

function Prop({
  label,
  value,
  mono,
  link,
}: {
  label: string;
  value: string;
  mono: boolean;
  link?: string;
}) {
  return (
    <div className={styles.prop}>
      <span className={styles.propLabel}>{label}</span>
      {link ? (
        <a href={link} target="_blank" rel="noopener noreferrer" className={`${styles.propValue} ${styles.propLink} ${mono ? "text-mono" : ""}`}>
          {value}
        </a>
      ) : (
        <span className={`${styles.propValue} ${mono ? "text-mono" : ""}`}>{value}</span>
      )}
    </div>
  );
}
