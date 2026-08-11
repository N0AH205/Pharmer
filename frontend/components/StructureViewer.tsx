"use client";

import { useState } from "react";
import type { ChemicalStructure } from "@/lib/types";
import CitationBadge from "./CitationBadge";
import styles from "./StructureViewer.module.css";

interface Props {
  structure: ChemicalStructure;
}

function formatChemicalFormula(formula: string): string {
  const subscripts: { [key: string]: string } = {
    "0": "₀", "1": "₁", "2": "₂", "3": "₃", "4": "₄",
    "5": "₅", "6": "₆", "7": "₇", "8": "₈", "9": "₉"
  };
  return formula.split("").map(char => subscripts[char] || char).join("");
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
        <table className={styles.structureTable}>
          <tbody>
            {structure.molecular_formula && (
              <tr>
                <td className={styles.tableLabel}>Formula</td>
                <td className={`${styles.tableValue} text-mono`}>
                  <strong>{formatChemicalFormula(structure.molecular_formula)}</strong>
                </td>
              </tr>
            )}
            {structure.molecular_weight && (
              <tr>
                <td className={styles.tableLabel}>Molecular weight</td>
                <td className={styles.tableValue}>
                  <strong>{structure.molecular_weight} g/mol</strong>
                </td>
              </tr>
            )}
            {structure.iupac_name && (
              <tr>
                <td className={styles.tableLabel}>IUPAC name</td>
                <td className={styles.tableValue}>{structure.iupac_name}</td>
              </tr>
            )}
            {structure.pubchem_cid && (
              <tr>
                <td className={styles.tableLabel}>PubChem CID</td>
                <td className={styles.tableValue}>
                  <a
                    href={`https://pubchem.ncbi.nlm.nih.gov/compound/${structure.pubchem_cid}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className={styles.tableLink}
                  >
                    {structure.pubchem_cid}
                  </a>
                </td>
              </tr>
            )}
            {structure.smiles && (
              <tr>
                <td className={styles.tableLabel}>SMILES</td>
                <td className={styles.tableValue}>
                  <code className={styles.codeBlock}>{structure.smiles}</code>
                </td>
              </tr>
            )}
            {structure.inchi && (
              <tr>
                <td className={styles.tableLabel}>InChI</td>
                <td className={styles.tableValue}>
                  <code className={styles.codeBlockMuted}>{structure.inchi}</code>
                </td>
              </tr>
            )}
          </tbody>
        </table>

        {structure.sources && structure.sources.length > 0 && (
          <div className={styles.citationContainer}>
            <CitationBadge citations={structure.sources} />
          </div>
        )}
      </div>
    </div>
  );
}
