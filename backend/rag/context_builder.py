"""
Context builder — Phase 2.5.

Responsibility: transform raw retriever chunks into an LLM-ready context
string and a source_map that the citation resolver will use.

SOURCE_N labels live here — NOT in retriever.py — because the same chunk can
be SOURCE_1 in one request and SOURCE_5 in another. The identifier is only
meaningful within the scope of a single prompt construction.

Usage in pipeline.py:

    chunks = await retriever.retrieve(query)
    context, source_map = build_context(chunks)
    # source_map = {"SOURCE_1": chunks[0], "SOURCE_2": chunks[1], …}
"""

from __future__ import annotations


def build_context(chunks: list[dict]) -> tuple[str, dict[str, dict]]:
    """
    Label each chunk SOURCE_N and format them into a single context string.

    Args:
        chunks: Raw chunk dicts from Retriever.retrieve().

    Returns:
        context   : Formatted string injected into the LLM system prompt.
        source_map: Dict mapping "SOURCE_1" … "SOURCE_N" → original chunk dict.
                    Used by citation_resolver.resolve_citations().
    """
    source_map: dict[str, dict] = {}
    parts: list[str] = []

    for i, chunk in enumerate(chunks):
        sid = f"SOURCE_{i + 1}"
        source_map[sid] = chunk

        header = (
            f"[{sid}]\n"
            f"Source : {chunk.get('source', 'Unknown')}\n"
            f"Field  : {chunk.get('field', 'general')}\n"
            f"URL    : {chunk.get('url', '')}\n"
        )
        body = chunk.get("text", "").strip()
        parts.append(f"{header}\n{body}")

    context = "\n\n---\n\n".join(parts)
    return context, source_map
