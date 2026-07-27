"""
RAG pipeline — Phase 3.

Orchestrates the full chain:
    PubChem → QueryBuilder → Retriever → ContextBuilder → LLM → CitationResolver → Pydantic

debug=True returns a separate debug object (retrieved chunks, source_map)
alongside the normal DrugInfo — without polluting the public API schema.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from rag.schema import DrugInfo, ChemicalStructure, Citation
from rag.retriever import get_retriever
from rag.context_builder import build_context
from rag.citation_resolver import resolve_field_citations
from rag.llm import generate_structured_output
from rag.query_builder import build_retrieval_query
from ingest.pubchem import enrich_structure

PROMPT_TEMPLATE = Path(__file__).parent.parent / "prompts" / "drug_info.txt"

# Fallback mock — used ONLY when retriever is empty (Phase 1 compatibility)
_MOCK_ASPIRIN_PATH = Path(__file__).parent / "_mock_aspirin.json"


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
        # Remove non-schema fields before Pydantic validation
        "common_name": None,
        "synonyms": None,
    }
    # Drop keys that don't exist in ChemicalStructure
    chem_keys = ChemicalStructure.model_fields.keys()
    raw_dict["chemical_structure"] = {
        k: v for k, v in raw_dict["chemical_structure"].items()
        if k in chem_keys
    }
    raw_dict["query_smiles"] = smiles

    # ── 9. Pydantic validation ────────────────────────────────────────────
    drug_info = DrugInfo(**raw_dict)

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
