"""
Citation resolver — Phase 2.5.

Responsibility: convert the LLM's internal SOURCE_N references into trusted
Citation objects backed by ingestion metadata.

The LLM returns source_ids (e.g. ["SOURCE_1", "SOURCE_3"]).
This module validates them against the source_map, discards any IDs that
the LLM hallucinated or that don't exist, deduplicates, and returns a clean
list of Citation objects with URLs we control.

Why this matters:
    Without this layer, the LLM could fabricate URLs or cite the wrong source.
    With it, citation integrity is guaranteed — the LLM only gets to say
    "I used SOURCE_1" and we look up what SOURCE_1 actually is.

Usage in pipeline.py:

    citations = resolve_citations(
        source_ids=field_dict.get("source_ids", []),
        source_map=source_map,
    )
"""

from __future__ import annotations

import logging

from rag.schema import Citation

logger = logging.getLogger(__name__)


def resolve_citations(
    source_ids: list[str] | None,
    source_map: dict[str, dict],
) -> list[Citation]:
    """
    Validate and resolve SOURCE_N IDs to trusted Citation objects.

    Args:
        source_ids: List of SOURCE_N strings returned by the LLM.
                    May contain invalid/hallucinated IDs — they are discarded.
        source_map: Dict of {"SOURCE_1": chunk, …} built by context_builder.

    Returns:
        Deduplicated list[Citation] with data sourced from ingestion metadata,
        not from the LLM's output.
    """
    if not source_ids:
        return []

    seen: set[str] = set()
    citations: list[Citation] = []

    for sid in source_ids:
        # Normalise in case the LLM wraps the ID in brackets or lowercase
        normalised = sid.strip().upper()
        if not normalised.startswith("SOURCE_"):
            normalised = f"SOURCE_{normalised}" if normalised.isdigit() else normalised

        if normalised in seen:
            continue  # deduplicate

        chunk = source_map.get(normalised)
        if chunk is None:
            logger.debug("Citation resolver: LLM returned unknown ID %r — discarded", sid)
            continue

        seen.add(normalised)
        citations.append(
            Citation(
                source=chunk.get("source", "Unknown source"),
                url=chunk.get("url") or None,
            )
        )

    return citations


def resolve_field_citations(
    llm_dict: dict,
    source_map: dict[str, dict],
    field_keys: list[str] | None = None,
) -> dict:
    """
    Walk through an LLM response dict, resolve source_ids → sources for every
    FieldValue-like sub-dict, and remove the internal source_ids key.

    Args:
        llm_dict:   Raw dict from the LLM (may contain source_ids).
        source_map: Built by context_builder.build_context().
        field_keys: Optional list of top-level keys to process.
                    Defaults to all FieldValue-like fields in DrugInfo.

    Returns:
        Modified dict safe to pass to DrugInfo(**…) for Pydantic validation.
    """
    if field_keys is None:
        field_keys = [
            "mechanism_of_action",
            "indications",
            "contraindications",
            "adverse_effects",
            "drug_interactions",
        ]

    result = dict(llm_dict)

    # 1. Top-level FieldValue fields
    for key in field_keys:
        field = result.get(key)
        if not isinstance(field, dict):
            # If LLM omitted the field or returned a string/null, default to missing FieldValue
            content_str = field if isinstance(field, str) else None
            field = {
                "content": content_str,
                "missing": content_str is None,
                "sources": [],
            }
            result[key] = field
            continue

        raw_ids = field.pop("source_ids", None)
        citations = resolve_citations(raw_ids, source_map)

        existing = field.get("sources", [])
        if citations:
            field["sources"] = [c.model_dump() for c in citations]
        elif not existing:
            field["sources"] = []

        if "missing" not in field:
            field["missing"] = field.get("content") is None

    # 2. ADME sub-fields
    adme = result.get("adme")
    if not isinstance(adme, dict):
        adme = {}

    for sub_key in ["absorption", "distribution", "metabolism", "excretion"]:
        sub = adme.get(sub_key)
        if not isinstance(sub, dict):
            content_str = sub if isinstance(sub, str) else None
            sub = {
                "content": content_str,
                "missing": content_str is None,
                "sources": [],
            }
            adme[sub_key] = sub
        else:
            raw_ids = sub.pop("source_ids", None)
            citations = resolve_citations(raw_ids, source_map)
            if citations:
                sub["sources"] = [c.model_dump() for c in citations]
            elif not sub.get("sources"):
                sub["sources"] = []
            if "missing" not in sub:
                sub["missing"] = sub.get("content") is None

    result["adme"] = adme

    # 3. Drug Name
    dn = result.get("drug_name")
    if isinstance(dn, str):
        result["drug_name"] = {
            "generic": dn,
            "brand_names": [],
            "sources": [],
        }
    elif isinstance(dn, dict):
        raw_ids = dn.pop("source_ids", None)
        citations = resolve_citations(raw_ids, source_map)
        if citations:
            dn["sources"] = [c.model_dump() for c in citations]
        elif not dn.get("sources"):
            dn["sources"] = []
        if dn.get("brand_names") is None:
            dn["brand_names"] = []
        if not dn.get("generic"):
            dn["generic"] = "Unknown"
    else:
        result["drug_name"] = {
            "generic": "Unknown",
            "brand_names": [],
            "sources": [],
        }

    return result
