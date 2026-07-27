/**
 * DrugInfo schema — TypeScript types matching the Python Pydantic backend schema.
 * Every field uses FieldValue, which carries the content, citations, and a
 * `missing` flag. When `missing` is true, the UI shows "Data not available"
 * rather than fabricated content.
 */

export interface Citation {
  source: string;       // e.g. "PubChem CID 2244", "DailyMed SPL 2023-04"
  url?: string;
  accessed_at?: string;
}

export interface FieldValue {
  content: string | null;
  sources: Citation[];
  missing: boolean;
}

export interface ADMEFields {
  absorption: FieldValue;
  distribution: FieldValue;
  metabolism: FieldValue;
  excretion: FieldValue;
}

export interface ChemicalStructure {
  smiles: string;
  inchi?: string;
  iupac_name?: string;
  molecular_formula?: string;
  molecular_weight?: number;
  pubchem_cid?: number;
  image_url?: string;
  sources: Citation[];
}

export interface DrugInfo {
  drug_name: {
    generic: string;
    brand_names: string[];
    sources: Citation[];
  };
  mechanism_of_action: FieldValue;
  adme: ADMEFields;
  chemical_structure: ChemicalStructure;
  indications: FieldValue;
  contraindications: FieldValue;
  adverse_effects: FieldValue;
  drug_interactions: FieldValue;
  disclaimer: string;
  query_smiles: string;
  generated_at: string;
}

export interface QueryRequest {
  smiles: string;
}

export interface QueryResponse {
  success: boolean;
  data?: DrugInfo;
  error?: string;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  smiles?: string;
  drugInfo?: DrugInfo;
  error?: string;
  timestamp: Date;
}
