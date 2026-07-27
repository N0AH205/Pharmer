import { NextRequest, NextResponse } from "next/server";
import type { DrugInfo, QueryResponse } from "@/lib/types";

/**
 * Phase 1 — Mock API route.
 * Returns a fully-formed DrugInfo object for Aspirin regardless of input,
 * so the UI can be developed and tested without a live LLM/vector DB.
 * Phase 3 will replace this with a proxy to the Python FastAPI backend.
 */

const MOCK_ASPIRIN: DrugInfo = {
  query_smiles: "CC(=O)Oc1ccccc1C(=O)O",
  generated_at: new Date().toISOString(),
  disclaimer:
    "This information is for educational and reference purposes only. It does not constitute clinical advice. Always consult a licensed clinician or pharmacist for patient-specific guidance.",
  drug_name: {
    generic: "Acetylsalicylic acid",
    brand_names: ["Aspirin", "Bayer Aspirin", "Ecotrin", "Bufferin"],
    sources: [
      { source: "PubChem CID 2244", url: "https://pubchem.ncbi.nlm.nih.gov/compound/2244" },
      { source: "DailyMed NDA 000019", url: "https://dailymed.nlm.nih.gov" },
    ],
  },
  chemical_structure: {
    smiles: "CC(=O)Oc1ccccc1C(=O)O",
    inchi: "InChI=1S/C9H8O4/c1-6(10)13-8-5-3-2-4-7(8)9(11)12/h2-5H,1H3,(H,11,12)",
    iupac_name: "2-acetoxybenzoic acid",
    molecular_formula: "C₉H₈O₄",
    molecular_weight: 180.16,
    pubchem_cid: 2244,
    image_url: "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/CID/2244/PNG",
    sources: [{ source: "PubChem CID 2244", url: "https://pubchem.ncbi.nlm.nih.gov/compound/2244" }],
  },
  mechanism_of_action: {
    content:
      "Acetylsalicylic acid irreversibly inhibits cyclooxygenase-1 (COX-1) and cyclooxygenase-2 (COX-2) enzymes through acetylation of a serine residue (Ser530 on COX-1, Ser516 on COX-2). This blocks the conversion of arachidonic acid to prostaglandin H₂ (PGH₂), reducing downstream synthesis of prostaglandins, prostacyclin, and thromboxane A₂. Inhibition of thromboxane A₂ in platelets is irreversible for the platelet's lifespan (~7–10 days), underpinning the antiplatelet effect used in cardiovascular prophylaxis.",
    missing: false,
    sources: [
      { source: "PubChem CID 2244 — Pharmacology", url: "https://pubchem.ncbi.nlm.nih.gov/compound/2244" },
    ],
  },
  adme: {
    absorption: {
      content:
        "Rapidly absorbed from the gastrointestinal tract, primarily in the stomach and upper small intestine. Bioavailability is approximately 50–68% due to first-pass hydrolysis to salicylate. Peak plasma concentrations of salicylate are reached within 1–2 hours. Enteric-coated formulations delay absorption to reduce gastric irritation.",
      missing: false,
      sources: [{ source: "DailyMed SPL — Aspirin", url: "https://dailymed.nlm.nih.gov" }],
    },
    distribution: {
      content:
        "Salicylate is widely distributed to body tissues and fluids including synovial fluid, CSF, and breast milk. Volume of distribution is ~0.17 L/kg at low doses. Plasma protein binding is 80–90% (albumin), concentration-dependent; binding decreases at higher doses.",
      missing: false,
      sources: [{ source: "DailyMed SPL — Aspirin", url: "https://dailymed.nlm.nih.gov" }],
    },
    metabolism: {
      content:
        "Rapidly hydrolyzed to salicylic acid in the GI mucosa, plasma, and liver. Salicylic acid is then conjugated in the liver with glycine (forming salicyluric acid, the major metabolite) and glucuronic acid. Exhibits non-linear (Michaelis-Menten) kinetics at high doses due to saturation of glycine conjugation.",
      missing: false,
      sources: [{ source: "DailyMed SPL — Aspirin", url: "https://dailymed.nlm.nih.gov" }],
    },
    excretion: {
      content:
        "Excreted primarily by the kidney. At low doses, half-life is 2–3 hours; at high anti-inflammatory doses, half-life extends to 15–30 hours due to metabolic saturation. Renal excretion of free salicylate is pH-dependent and increases markedly in alkaline urine (alkaline diuresis used in salicylate toxicity management).",
      missing: false,
      sources: [{ source: "DailyMed SPL — Aspirin", url: "https://dailymed.nlm.nih.gov" }],
    },
  },
  indications: {
    content:
      "• Mild-to-moderate pain (analgesic)\n• Fever reduction (antipyretic)\n• Inflammation (e.g. rheumatoid arthritis, acute rheumatic fever)\n• Antiplatelet: secondary prevention of myocardial infarction and ischemic stroke\n• Primary prevention of cardiovascular events (selected high-risk patients)\n• Kawasaki disease (high-dose, acute phase)\n• Pre-eclampsia prevention (low-dose, per USPSTF guidelines)",
    missing: false,
    sources: [
      { source: "FDA-approved labeling — DailyMed", url: "https://dailymed.nlm.nih.gov" },
    ],
  },
  contraindications: {
    content:
      "• Hypersensitivity to aspirin or other NSAIDs (including aspirin-exacerbated respiratory disease / Samter's triad)\n• Children and teenagers with viral illness (Reye's syndrome risk)\n• Active peptic ulcer disease or GI bleeding\n• Hemophilia or other bleeding disorders\n• Severe hepatic or renal impairment\n• Third trimester of pregnancy (risk of premature closure of ductus arteriosus, neonatal bleeding)\n• Concomitant use of methotrexate (high dose)",
    missing: false,
    sources: [
      { source: "FDA-approved labeling — DailyMed", url: "https://dailymed.nlm.nih.gov" },
    ],
  },
  adverse_effects: {
    content:
      "Common:\n• GI irritation, nausea, dyspepsia\n• Occult GI blood loss\n• Tinnitus (at high doses — early sign of salicylism)\n\nSerious:\n• GI ulceration and hemorrhage\n• Hypersensitivity reactions (urticaria, bronchospasm, anaphylaxis)\n• Salicylate toxicity / salicylism (tinnitus, vertigo, hyperventilation, metabolic acidosis)\n• Reye's syndrome (children with viral illness)\n• Bleeding (surgical or traumatic)\n• Aspirin-exacerbated respiratory disease (AERD)",
    missing: false,
    sources: [
      { source: "FDA-approved labeling — DailyMed", url: "https://dailymed.nlm.nih.gov" },
    ],
  },
  drug_interactions: {
    content:
      "• **Warfarin / anticoagulants** — increased bleeding risk; avoid or monitor INR closely\n• **Other NSAIDs / ibuprofen** — ibuprofen may antagonize the antiplatelet effect of low-dose aspirin\n• **Methotrexate** — aspirin reduces renal clearance; risk of methotrexate toxicity\n• **ACE inhibitors** — may reduce antihypertensive effect\n• **SSRIs** — additive bleeding risk (platelet serotonin depletion)\n• **Corticosteroids** — increased GI ulceration risk\n• **Valproic acid** — aspirin displaces valproate from protein binding; may increase valproate toxicity\n• **Probenecid / uricosurics** — aspirin antagonizes uricosuric effect at doses >2 g/day",
    missing: false,
    sources: [
      { source: "FDA-approved labeling — DailyMed", url: "https://dailymed.nlm.nih.gov" },
      { source: "PubChem CID 2244", url: "https://pubchem.ncbi.nlm.nih.gov/compound/2244" },
    ],
  },
};

export async function POST(req: NextRequest) {
  const body = await req.json().catch(() => null);

  if (!body?.smiles || typeof body.smiles !== "string") {
    return NextResponse.json(
      { success: false, error: "Missing or invalid 'smiles' field" } satisfies QueryResponse,
      { status: 400 }
    );
  }

  // Simulate network latency (Phase 1 mock)
  await new Promise((r) => setTimeout(r, 1400));

  const response: QueryResponse = {
    success: true,
    data: {
      ...MOCK_ASPIRIN,
      query_smiles: body.smiles,
      generated_at: new Date().toISOString(),
    },
  };

  return NextResponse.json(response);
}
