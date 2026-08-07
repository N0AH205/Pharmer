"""
RAG pipeline — Phase 3.

Orchestrates the full chain:
    PubChem → QueryBuilder → Retriever → ContextBuilder → LLM → CitationResolver → Pydantic

debug=True returns a separate debug object (retrieved chunks, source_map)
alongside the normal DrugInfo — without polluting the public API schema.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from rag.schema import (
    DrugInfo, DrugName, ChemicalStructure, Citation,
    FieldValue, ADMEFields, PharmacodynamicsFields,
    ToxicologyFields, TherapeuticProfile, HistoryFields,
)
from rag.retriever import get_retriever
from rag.context_builder import build_context
from rag.citation_resolver import resolve_field_citations
from rag.llm import generate_structured_output
from rag.query_builder import build_retrieval_query
from ingest.pubchem import enrich_structure

PROMPT_TEMPLATE = Path(__file__).parent.parent / "prompts" / "drug_info.txt"

logger = logging.getLogger(__name__)

_MISSING = FieldValue(content=None, missing=True)


async def run_pipeline(
    smiles: str,
    debug: bool = False,
) -> DrugInfo | dict[str, Any]:
    """
    Full RAG pipeline: SMILES → structured DrugInfo.

    Args:
        smiles: A valid SMILES string.
        debug:  If True, returns a dict:
                    {
                        "result": DrugInfo.model_dump(),
                        "debug": {
                            "retrieved_chunks": [...],
                            "source_map_keys": [...],
                            "query": "...",
                        }
                    }
                If False (default), returns DrugInfo directly.

    Raises:
        ValueError: If the LLM returns malformed JSON.
        pydantic.ValidationError: If the LLM output doesn't match DrugInfo.
    """
    retriever = get_retriever()

    # ── 1. PubChem: resolve SMILES → drug identity ────────────────────────
    structure_data = await enrich_structure(smiles)

    # ── 2. Build retrieval query using common name + IUPAC + synonyms ─────
    query = build_retrieval_query(structure_data, field=None)

    # ── 3. Retrieve relevant chunks from ChromaDB ─────────────────────────
    if not retriever.is_ready():
        # Knowledge base is empty — fall back to mock (development only)
        from rag.pipeline_mock import MOCK_ASPIRIN
        return MOCK_ASPIRIN.model_copy(update={"query_smiles": smiles})

    # Use the stable PubChem CID as the metadata filter for two-stage retrieval:
    # Stage 1 — only this drug's chunks; Stage 2 — rank by semantic similarity.
    pubchem_cid = str(structure_data.get("pubchem_cid") or "")
    chunks = await retriever.retrieve(
        query,
        n_results=8,
        pubchem_cid=pubchem_cid or None,
    )


    if not chunks:
        raise ValueError(
            f"ChromaDB returned 0 chunks for query {query!r}. "
            "Run python -m ingest.run_ingest to populate the knowledge base."
        )

    # ── 4. Build labelled context + source_map ────────────────────────────
    context, source_map = build_context(chunks)

    # ── 5. Load and fill prompt template ──────────────────────────────────
    template = PROMPT_TEMPLATE.read_text(encoding="utf-8")
    drug_name = (
        structure_data.get("common_name")
        or structure_data.get("iupac_name")
        or smiles
    )
    system_prompt = (
        template
        .replace("{context}", context)
        .replace("{smiles}", smiles)
        .replace("{drug_name}", drug_name)
    )
    user_message = (
        f"Drug SMILES: {smiles}\n"
        f"Drug name: {drug_name}\n"
        f"IUPAC name: {structure_data.get('iupac_name', 'unknown')}"
    )

    # ── 6. Call LLM ───────────────────────────────────────────────────────
    raw_dict = await generate_structured_output(
        system_prompt=system_prompt,
        user_message=user_message,
        output_schema=DrugInfo,
    )

    # ── 7. Resolve source_ids → trusted Citations ─────────────────────────
    raw_dict = resolve_field_citations(raw_dict, source_map)

    # ── 8. Inject trusted PubChem structure (never from LLM) ─────────────
    raw_dict["chemical_structure"] = {
        **structure_data,
        "common_name": None,
        "synonyms": None,
    }
    chem_keys = ChemicalStructure.model_fields.keys()
    raw_dict["chemical_structure"] = {
        k: v for k, v in raw_dict["chemical_structure"].items()
        if k in chem_keys
    }
    raw_dict["query_smiles"] = smiles

    # ── 9. Pydantic validation — graceful degradation on LLM misformat ────
    try:
        drug_info = DrugInfo(**raw_dict)
    except (ValidationError, Exception) as exc:
        logger.error(
            "Pydantic validation failed for SMILES %r — returning safe fallback. Error: %s",
            smiles, exc,
        )
        # Build a structurally valid DrugInfo where all LLM fields are missing.
        # The user sees 'Data unavailable' rather than a 500 error.
        drug_info = DrugInfo(
            query_smiles=smiles,
            drug_name=DrugName(
                generic=structure_data.get("common_name") or structure_data.get("iupac_name") or smiles,
                brand_names=[],
                lab_codes=[],
                sources=[],
            ),
            chemical_structure=ChemicalStructure(
                **{k: v for k, v in {
                    **structure_data,
                    "common_name": None,
                    "synonyms": None,
                }.items() if k in ChemicalStructure.model_fields}
            ),
            therapeutic_classes=_MISSING,
            pharmacodynamics=PharmacodynamicsFields(
                mechanism_of_action=_MISSING,
                physiologic_effect=_MISSING,
                binding_affinity=_MISSING,
                selectivity=_MISSING,
                potency=_MISSING,
                efficacy=_MISSING,
            ),
            adme=ADMEFields(
                absorption=_MISSING,
                distribution=_MISSING,
                metabolism=_MISSING,
                excretion=_MISSING,
            ),
            toxicology=ToxicologyFields(
                ld50=_MISSING,
                toxic_doses=_MISSING,
                organ_toxicity=_MISSING,
                overdose_management=_MISSING,
            ),
            therapeutic_profile=TherapeuticProfile(
                indications=_MISSING,
                contraindications=_MISSING,
                adverse_effects=_MISSING,
                drug_interactions=_MISSING,
            ),
            history=HistoryFields(
                background=_MISSING,
                discovery=_MISSING,
                development=_MISSING,
                clinical_trials=_MISSING,
            ),
        )

    if debug:
        return {
            "result": drug_info.model_dump(),
            "debug": {
                "query": query,
                "retrieved_chunks": [
                    {k: v for k, v in c.items() if k != "text"}
                    for c in chunks
                ],
                "source_map_keys": list(source_map.keys()),
                "chunk_count": retriever.chunk_count(),
            },
        }

    return drug_info
