"""
Pydantic schema for the structured drug-information output.

Every content field uses FieldValue, which carries:
  - content: the actual text (None if missing)
  - sources: list of citations
  - missing: True if data was not found — the LLM must NOT fabricate

This schema is also serialised as a JSON Schema and injected into the
system prompt so the LLM knows the exact structure to output (Phase 3).
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class Citation(BaseModel):
    source: str
    url: Optional[str] = None
    accessed_at: Optional[str] = None


class FieldValue(BaseModel):
    """
    A single output field. If data is unavailable, set missing=True
    and content=None. NEVER fabricate content.
    """
    content: Optional[str] = None
    sources: list[Citation] = Field(default_factory=list)
    missing: bool = False


class ADMEFields(BaseModel):
    absorption: FieldValue
    distribution: FieldValue
    metabolism: FieldValue
    excretion: FieldValue


class ChemicalStructure(BaseModel):
    smiles: str
    inchi: Optional[str] = None
    iupac_name: Optional[str] = None
    molecular_formula: Optional[str] = None
    molecular_weight: Optional[float] = None
    pubchem_cid: Optional[int] = None
    image_url: Optional[str] = None
    sources: list[Citation] = Field(default_factory=list)


class DrugName(BaseModel):
    generic: str
    brand_names: list[str] = Field(default_factory=list)
    sources: list[Citation] = Field(default_factory=list)


class DrugInfo(BaseModel):
    """
    Full structured drug-information output.
    Returned by the RAG pipeline for every SMILES query.
    """
    query_smiles: str
    generated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    disclaimer: str = (
        "This information is for educational and reference purposes only. "
        "It does not constitute clinical advice. Always consult a licensed "
        "clinician or pharmacist for patient-specific guidance."
    )
    drug_name: DrugName
    mechanism_of_action: FieldValue
    adme: ADMEFields
    chemical_structure: ChemicalStructure
    indications: FieldValue
    contraindications: FieldValue
    adverse_effects: FieldValue
    drug_interactions: FieldValue


class QueryRequest(BaseModel):
    smiles: str = Field(..., min_length=1, description="A valid SMILES string")
