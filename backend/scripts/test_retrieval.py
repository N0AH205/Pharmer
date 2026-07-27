"""
Standalone retrieval validation script — Phase 2.5 gate.

Tests the retrieval layer independently of the LLM.
Uses two-stage retrieval: metadata filter (pubchem_cid) → vector similarity.

Usage:
    cd backend
    python -m scripts.test_retrieval --drug "Aspirin"
    python -m scripts.test_retrieval --smiles "CC(=O)Oc1ccccc1C(=O)O"
    python -m scripts.test_retrieval --drug "Aspirin" --n 12
    python -m scripts.test_retrieval --drug "Aspirin" --field adme
    python -m scripts.test_retrieval --inspect          # show all DB contents
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
import textwrap
from collections import defaultdict

# Force UTF-8 stream handling on Windows console
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from ingest.pubchem import enrich_structure, get_compound_by_smiles, get_synonyms
from rag.query_builder import build_retrieval_query
from rag.retriever import get_retriever

# -- Console colours -----------------------------------------------------------

BOLD   = "\033[1m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"
CYAN   = "\033[96m"
DIM    = "\033[2m"
RESET  = "\033[0m"

EXPECTED_FIELDS = [
    "indications", "contraindications", "adverse_effects",
    "drug_interactions", "pharmacology", "clinical_pharmacology",
    "mechanism_of_action", "pharmacokinetics", "research",
]


def _bar(distance: float, width: int = 20) -> str:
    filled = max(0, width - int(distance * width / 2))
    return f"[{'|' * filled}{'.' * (width - filled)}] {distance:.3f}"


def _preview(text: str, chars: int = 180) -> str:
    collapsed = " ".join(text.split())
    return collapsed[:chars] + ("..." if len(collapsed) > chars else "")


def _color_d(d: float) -> str:
    if d < 0.35:  return GREEN
    if d < 0.60:  return YELLOW
    return RED


# -- DB inspection -------------------------------------------------------------

def inspect_db():
    """Print a table of every chunk in the database, grouped by drug + field."""
    retriever = get_retriever()
    count = retriever.chunk_count()
    print(f"\n{BOLD}ChromaDB Contents{RESET} ({count} total chunks)\n")

    if count == 0:
        print(f"{RED}Collection is empty. Run: python -m ingest.run_ingest{RESET}")
        return

    all_items = retriever.collection.get(include=["metadatas"])
    metadatas = all_items["metadatas"]

    summary: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    cid_map: dict[str, str] = {}
    for meta in metadatas:
        drug = meta.get("drug", "unknown")
        field = meta.get("field", "unknown")
        cid = meta.get("pubchem_cid", "")
        summary[drug][field] += 1
        if drug not in cid_map:
            cid_map[drug] = cid

    print(f"{'Drug':<22} {'CID':<10} {'Field':<30} {'N':>4}")
    print("-" * 72)
    for drug in sorted(summary):
        cid = cid_map.get(drug, "")
        for field in sorted(summary[drug]):
            n = summary[drug][field]
            tick = GREEN + "+" + RESET if n > 0 else RED + "-" + RESET
            print(f"  {tick} {drug:<20} {cid:<10} {field:<30} {n:>4}")
    print("-" * 72)
    print(f"Total: {count} chunks across {len(summary)} drugs")
    print()


# -- Core retrieval test -------------------------------------------------------

async def run(
    drug_name: str | None,
    smiles: str | None,
    n: int,
    field: str | None,
):
    retriever = get_retriever()

    print(f"\n{BOLD}PharmaRAG — Retrieval Test{RESET}")
    print("-" * 62)

    count = retriever.chunk_count()
    print(f"ChromaDB       : {os.getenv('CHROMA_PATH', '../data/chroma')}")
    print(f"Total chunks   : {BOLD}{count}{RESET}")
    if count == 0:
        print(f"\n{RED}Collection is empty. Run: python -m ingest.run_ingest{RESET}")
        sys.exit(1)

    # -- Resolve drug identity ----------------------------------------------
    pubchem_cid: str | None = None
    resolved_name: str = drug_name or smiles or ""

    if smiles:
        print(f"\nResolving SMILES via PubChem...")
        props = await get_compound_by_smiles(smiles)
        if not props:
            print(f"{RED}PubChem could not resolve SMILES: {smiles!r}{RESET}")
            sys.exit(1)
        cid_int = props.get("CID")
        pubchem_cid = str(cid_int)
        syns = await get_synonyms(cid_int, max_synonyms=5)
        resolved_name = syns[0] if syns else (props.get("IUPACName") or smiles)
        structure_data = {
            "common_name": resolved_name,
            "iupac_name": props.get("IUPACName"),
            "synonyms": syns,
            "smiles": smiles,
        }
        print(f"  CID : {pubchem_cid}")
        print(f"  Name: {resolved_name}")
    elif drug_name:
        # Try to find the CID by looking at what's stored in the DB
        all_meta = retriever.collection.get(include=["metadatas"])["metadatas"]
        for meta in all_meta:
            stored_drug = meta.get("drug", "").lower()
            if drug_name.lower() in stored_drug or stored_drug in drug_name.lower():
                pubchem_cid = meta.get("pubchem_cid") or None
                resolved_name = meta.get("drug", drug_name)
                break
        structure_data = {
            "common_name": drug_name,
            "iupac_name": None,
            "synonyms": [],
            "smiles": "",
        }

    drug_pool = retriever.get_drug_chunk_count(pubchem_cid) if pubchem_cid else count
    query = build_retrieval_query(structure_data, field=field)

    print(f"\n{BOLD}Query{RESET}          : {CYAN}{query!r}{RESET}")
    if pubchem_cid:
        print(f"CID filter     : {pubchem_cid} ({drug_pool} chunks in this drug's pool)")
    else:
        print(f"{YELLOW}No CID filter — searching all {count} chunks (cross-drug results likely){RESET}")
    print(f"Requested n    : {n}")

    # -- Retrieve -----------------------------------------------------------
    print(f"\n{'-' * 62}")
    print(f"{BOLD}Retrieving top {n} chunks…{RESET}\n")

    chunks = await retriever.retrieve(query, n_results=n, pubchem_cid=pubchem_cid)

    if not chunks:
        print(f"{RED}Retriever returned 0 chunks.{RESET}")
        if pubchem_cid:
            print(f"Check: does CID {pubchem_cid} have any chunks?")
            print(f"  Run: python -m scripts.test_retrieval --inspect")
        sys.exit(1)

    # -- Print ranked results -----------------------------------------------
    for i, chunk in enumerate(chunks, 1):
        d = chunk["distance"]
        color = _color_d(d)
        print(f"{BOLD}Rank {i:>2}{RESET}  {color}{_bar(d)}{RESET}")
        print(f"  Drug   : {chunk.get('drug', '—')}")
        print(f"  Field  : {chunk.get('field', '—')}")
        print(f"  Source : {chunk.get('source', '—')}")
        print(f"  Preview: {DIM}{_preview(chunk.get('text', ''))}{RESET}")
        print()

    # -- Coverage report ----------------------------------------------------
    print(f"{'-' * 62}")
    print(f"{BOLD}Coverage for '{resolved_name}' (top {n} results){RESET}\n")

    # Drug distribution
    drug_counts: dict[str, int] = {}
    for chunk in chunks:
        d = chunk.get("drug", "unknown")
        drug_counts[d] = drug_counts.get(d, 0) + 1

    print("  Drug distribution:")
    for drug, cnt in sorted(drug_counts.items(), key=lambda x: -x[1]):
        is_correct = drug.lower() == resolved_name.lower() or (
            resolved_name.lower() in drug.lower() or drug.lower() in resolved_name.lower()
        )
        marker = GREEN if is_correct else RED
        print(f"    {marker}{drug:<28}{RESET}  {cnt} chunk(s)")

    # Field coverage (fixed — iterate fields once, not chunks × fields)
    field_counts: dict[str, int] = {}
    for chunk in chunks:
        f = chunk.get("field", "unknown")
        field_counts[f] = field_counts.get(f, 0) + 1

    all_fields = sorted(set(EXPECTED_FIELDS) | set(field_counts.keys()))
    print("\n  Field coverage:")
    for f in all_fields:
        cnt = field_counts.get(f, 0)
        tick = f"{GREEN}+" if cnt > 0 else f"{RED}-"
        print(f"    {tick}{RESET}  {f:<32}  {cnt} chunk(s)")

    # -- Pass/fail summary --------------------------------------------------
    print(f"\n{'-' * 62}")
    issues: list[str] = []
    passes: list[str] = []

    # Acceptance criterion 1: 100% drug identity (most important)
    if pubchem_cid:
        wrong_drug_chunks = [c for c in chunks if c.get("pubchem_cid") != pubchem_cid]
        if wrong_drug_chunks:
            issues.append(
                f"{len(wrong_drug_chunks)}/{len(chunks)} chunks are from the wrong drug "
                f"(CID filter may not be working)"
            )
        else:
            passes.append(f"Drug identity: 100% of {len(chunks)} chunks are CID {pubchem_cid}")
    else:
        same_drug = sum(1 for c in chunks if resolved_name.lower() in c.get("drug", "").lower())
        pct = same_drug / len(chunks) * 100
        if pct < 100:
            issues.append(
                f"Only {same_drug}/{len(chunks)} ({pct:.0f}%) chunks are about '{resolved_name}' "
                f"(no CID filter applied)"
            )
        else:
            passes.append(f"Drug distribution: 100% correct (no filter)")

    # Acceptance criterion 2: field diversity
    distinct = len(field_counts)
    if distinct < 2:
        issues.append(f"Only {distinct} distinct field type(s) — ingest more data sources")
    else:
        passes.append(f"Field diversity: {distinct} distinct field types")

    # Acceptance criterion 3: top result distance
    top_d = chunks[0]["distance"]
    if top_d > 0.6:
        issues.append(f"Top distance {top_d:.3f} > 0.6 — embedding mismatch likely")
    else:
        passes.append(f"Top distance: {top_d:.3f} (acceptable)")

    for p in passes:
        print(f"  {GREEN}+{RESET} {p}")
    for issue in issues:
        print(f"  {RED}-{RESET} {issue}")

    if not issues:
        print(f"\n{GREEN}{BOLD}Gate 2 PASS{RESET} — retrieval is ready for LLM integration")
    else:
        print(f"\n{YELLOW}{BOLD}Gate 2 FAIL{RESET} — fix issues above before proceeding to LLM")
    print()


# -- Entry point ---------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Test ChromaDB retrieval independently of the LLM.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            examples:
              python -m scripts.test_retrieval --inspect
              python -m scripts.test_retrieval --drug "Aspirin"
              python -m scripts.test_retrieval --smiles "CC(=O)Oc1ccccc1C(=O)O"
              python -m scripts.test_retrieval --drug "Ibuprofen" --n 12
              python -m scripts.test_retrieval --drug "Aspirin" --field adme
        """),
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--drug",    help="Drug common name (e.g. 'Aspirin')")
    group.add_argument("--smiles",  help="SMILES string (resolved via PubChem)")
    group.add_argument("--inspect", action="store_true", help="Print full DB contents")
    parser.add_argument("--n",      type=int, default=8, help="Number of results (default: 8)")
    parser.add_argument("--field",  default=None,
                        help="Field context: moa|indications|adme|adverse_effects|drug_interactions")
    args = parser.parse_args()

    if args.inspect:
        inspect_db()
    else:
        asyncio.run(run(args.drug, args.smiles, args.n, args.field))


if __name__ == "__main__":
    main()
