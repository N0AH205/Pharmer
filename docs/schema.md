# Output Schema — Field Definitions

Reference document for the pharmacology domain expert.
Describes what each output field should contain, acceptable sources, and what
qualifies as "missing data" (triggers `missing: true` rather than fabrication).

---

## drug_name

| Sub-field | Content | Acceptable Sources |
|---|---|---|
| `generic` | INN / USAN generic name | PubChem, DailyMed |
| `brand_names` | Marketed brand name(s) | DailyMed, FDA Orange Book |

**Missing condition**: If the SMILES cannot be resolved to a known approved drug, `generic` should be the best available IUPAC name from PubChem with a note that no approved drug name was found.

---

## mechanism_of_action

**Content**: Molecular mechanism — receptor/enzyme target, type of interaction (agonist/antagonist/inhibitor/inducer), downstream biological effects. Avoid vague statements like "blocks receptor" — specify which receptor and what effect.

**Acceptable sources**: DailyMed SPL (pharmacology section), PubChem pharmacology text, DrugBank (when available), primary literature (PubMed).

**Missing condition**: If no mechanism is described in the retrieved context.

---

## adme

### absorption
**Content**: Route(s) of administration, bioavailability (%), time to peak (Tmax), food effects, rate-limiting factors.

### distribution
**Content**: Volume of distribution (Vd), plasma protein binding (%), tissue distribution notes, CNS penetration if relevant.

### metabolism
**Content**: Primary metabolic pathway(s), enzymes involved (CYP isoforms, UGT, etc.), active metabolites, first-pass effect.

### excretion
**Content**: Primary route of elimination, half-life (t½), renal vs. hepatic clearance, relevant patient factors (renal/hepatic impairment adjustments).

**Acceptable sources**: DailyMed SPL (clinical pharmacology section), DrugBank, PubMed pharmacokinetic studies.

**Missing condition**: If no pharmacokinetic data is present in retrieved context. Each sub-field (A, D, M, E) may independently be missing.

---

## chemical_structure

**Content**: Pulled from PubChem via SMILES resolution. All sub-fields come from PubChem CID lookup.

**Missing condition**: If the SMILES is not found in PubChem (exotic/novel compounds). In this case `pubchem_cid` and `image_url` will be null.

---

## indications

**Content**: FDA-approved uses only (unless context specifies off-label with explicit source). List format preferred.

**Acceptable sources**: DailyMed SPL (indications section), FDA drug label.

**Missing condition**: If drug is not FDA-approved or label is not in retrieved context.

---

## contraindications

**Content**: Absolute contraindications from FDA labeling. Include specific populations (pediatric, pregnancy, renal/hepatic impairment) and co-medications.

**Acceptable sources**: DailyMed SPL (contraindications section).

**Missing condition**: If no contraindication data is in retrieved context.

---

## adverse_effects

**Content**: Organized by frequency (common, serious/rare). Include specific thresholds where possible (e.g., "occurs in >10% of patients"). Do NOT include effects not listed in the retrieved context.

**Acceptable sources**: DailyMed SPL (adverse reactions section).

**Missing condition**: If no adverse effects data is in retrieved context.

---

## drug_interactions

**Content**: Clinically significant interactions only. For each interaction: the interacting drug/class, the mechanism (if known), and the clinical consequence (e.g., increased bleeding risk, reduced efficacy). Severity (major/moderate/minor) if available.

**Acceptable sources**: DailyMed SPL (drug interactions section), DrugBank, PubMed.

**Missing condition**: If no interaction data is in retrieved context.

---

## General Rules

- Every field value with `missing: false` MUST have at least one citation in `sources`.
- `missing: true` fields MUST have `content: null`.
- Never extrapolate or interpolate from related drugs — only report what is explicitly stated in the source.
- If two sources conflict, cite both and note the discrepancy in the content field.
