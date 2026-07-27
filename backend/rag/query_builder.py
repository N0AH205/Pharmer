"""
Retrieval query builder — Phase 2.5.

Constructs an optimised semantic query string from a drug's known names
(common name > IUPAC name > synonyms) combined with a field-specific suffix.

This module is the extensibility hook for field-specific retrieval (Phase 4).
Today every call passes field=None. Later, pipeline.py can call:

    build_retrieval_query(structure_data, field="adme")

to retrieve pharmacokinetics-focused chunks separately from mechanism chunks.
"""

from __future__ import annotations

# Semantic suffixes per retrieval field.
# None = general / default (used for the single-pass Phase 3 retrieval).
FIELD_SUFFIXES: dict[str | None, str] = {
    None:              "pharmacology mechanism clinical",
    "moa":             "mechanism of action inhibitor receptor target",
    "indications":     "indications therapeutic use treatment",
    "contraindications": "contraindications warnings precautions",
    "adverse_effects": "adverse effects side effects toxicity",
    "drug_interactions": "drug interactions clinical pharmacology",
    "adme":            "absorption distribution metabolism excretion pharmacokinetics",
}


def build_retrieval_query(
    structure_data: dict,
    field: str | None = None,
) -> str:
    """
    Build a semantic query string for ChromaDB retrieval.

    Name priority:
        1. common_name  (e.g. "Aspirin")        ← most likely to match documents
        2. iupac_name   (e.g. "2-acetoxybenzoic acid")
        3. up to 2 additional synonyms

    Args:
        structure_data: dict returned by ingest.pubchem.enrich_structure()
        field:          Optional field key from FIELD_SUFFIXES.
                        None → general pharmacology query (Phase 3 default).

    Returns:
        A space-separated query string such as:
            "Aspirin acetylsalicylic acid pharmacology mechanism clinical"
    """
    name_parts: list[str] = []

    common = structure_data.get("common_name")
    iupac = structure_data.get("iupac_name")
    synonyms: list[str] = structure_data.get("synonyms", [])

    # Build ordered name list: common first, then IUPAC, then fill from synonyms
    if common:
        name_parts.append(common)

    if iupac and iupac.lower() not in {n.lower() for n in name_parts}:
        name_parts.append(iupac)

    for syn in synonyms:
        if len(name_parts) >= 3:
            break
        if syn.lower() not in {n.lower() for n in name_parts}:
            name_parts.append(syn)

    # Fallback: if we got nothing from PubChem, use the raw SMILES
    if not name_parts:
        smiles = structure_data.get("smiles", "")
        name_parts.append(smiles)

    suffix = FIELD_SUFFIXES.get(field, FIELD_SUFFIXES[None])
    query = " ".join(name_parts[:3])
    return f"{query} {suffix}".strip()
