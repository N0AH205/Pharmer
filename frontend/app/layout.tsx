import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "PharmaRAG — Structured Drug Information",
  description:
    "A Retrieval-Augmented Generation tool for structured, cited drug-information queries. Enter a SMILES string to retrieve Mechanism of Action, ADME, Chemical Structure, Indications, Contraindications, Adverse Effects, and Drug Interactions.",
  keywords: ["drug information", "pharmacology", "RAG", "SMILES", "pharmaceutical"],
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
