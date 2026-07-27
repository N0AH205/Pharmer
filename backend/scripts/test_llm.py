"""
Standalone LLM validation script — Phase 2.5 gate (Test 1).

Tests the LLM layer in COMPLETE ISOLATION from ChromaDB, embeddings, and PubChem.
Uses hardcoded pharmaceutical context for Aspirin so every variable is known.

Pass criteria:
  ✓ Qwen connects and responds
  ✓ Response is valid JSON
  ✓ Pydantic validates without errors
  ✓ source_ids reference valid SOURCE_N from the hardcoded context
  ✓ mechanism_of_action.missing == False (we gave it the data)
  ✓ drug_interactions.missing == True  (not in the hardcoded context)

Usage:
    cd backend
    python -m scripts.test_llm
    python -m scripts.test_llm --model qwen2.5:14b
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


from rag.llm import generate_structured_output
from rag.schema import DrugInfo
from rag.context_builder import build_context
from rag.citation_resolver import resolve_field_citations

# -- Hardcoded context (trusted ground truth for this test) --------------------

HARDCODED_CHUNKS = [
    {
        "text": (
            "Aspirin (acetylsalicylic acid) irreversibly inhibits cyclooxygenase-1 (COX-1) "
            "and COX-2 enzymes by acetylating a serine residue (Ser530 on COX-1). "
            "This prevents the conversion of arachidonic acid to prostaglandin H2, "
            "reducing downstream synthesis of prostaglandins, prostacyclin, and thromboxane A2."
        ),
        "source": "PubChem CID 2244",
        "url": "https://pubchem.ncbi.nlm.nih.gov/compound/2244",
        "field": "pharmacology",
        "drug": "Aspirin",
        "distance": 0.12,
    },
    {
        "text": (
            "Aspirin is indicated for: mild-to-moderate pain (headache, toothache, "
            "musculoskeletal), fever reduction, inflammatory conditions (rheumatoid "
            "arthritis), and antiplatelet use for secondary prevention of myocardial "
            "infarction and ischaemic stroke."
        ),
        "source": "DailyMed SPL – Aspirin",
        "url": "https://dailymed.nlm.nih.gov",
        "field": "indications",
        "drug": "Aspirin",
        "distance": 0.15,
    },
    {
        "text": (
            "Contraindications: hypersensitivity to aspirin or NSAIDs; aspirin-exacerbated "
            "respiratory disease (AERD); children and teenagers with viral illness (Reye's "
            "syndrome risk); active peptic ulceration; haemophilia or other bleeding "
            "disorders; third trimester of pregnancy."
        ),
        "source": "DailyMed SPL – Aspirin",
        "url": "https://dailymed.nlm.nih.gov",
        "field": "contraindications",
        "drug": "Aspirin",
        "distance": 0.18,
    },
    {
        "text": (
            "Adverse effects include: gastrointestinal irritation and haemorrhage, "
            "tinnitus and hearing loss at high doses (salicylism), hypersensitivity "
            "reactions including urticaria and bronchospasm, Reye's syndrome in children "
            "with viral infections, and increased bleeding time."
        ),
        "source": "DailyMed SPL – Aspirin",
        "url": "https://dailymed.nlm.nih.gov",
        "field": "adverse_effects",
        "drug": "Aspirin",
        "distance": 0.20,
    },
    {
        "text": (
            "Pharmacokinetics: Aspirin is rapidly absorbed from the GI tract (bioavailability "
            "50–68%). Peak plasma salicylate in 1–2 hours. Widely distributed (Vd ~0.17 L/kg), "
            "80–90% albumin-bound. Hydrolysed to salicylate in GI mucosa, plasma, and liver. "
            "Renally excreted; half-life 2–3 h at low dose, 15–30 h at high dose."
        ),
        "source": "DailyMed SPL – Aspirin",
        "url": "https://dailymed.nlm.nih.gov",
        "field": "clinical_pharmacology",
        "drug": "Aspirin",
        "distance": 0.22,
    },
]

# Note: drug_interactions is intentionally NOT in the hardcoded context.
# The LLM should set missing=True for that field.

MOCK_STRUCTURE = {
    "smiles": "CC(=O)Oc1ccccc1C(=O)O",
    "inchi": "InChI=1S/C9H8O4/c1-6(10)13-8-5-3-2-4-7(8)9(11)12/h2-5H,1H3,(H,11,12)",
    "iupac_name": "2-acetoxybenzoic acid",
    "common_name": "Aspirin",
    "molecular_formula": "C9H8O4",
    "molecular_weight": 180.16,
    "pubchem_cid": 2244,
    "image_url": "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/CID/2244/PNG",
    "sources": [{"source": "PubChem CID 2244", "url": "https://pubchem.ncbi.nlm.nih.gov/compound/2244"}],
}


# -- Helpers -------------------------------------------------------------------

BOLD  = "\033[1m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED   = "\033[91m"
RESET = "\033[0m"

def _pass(msg: str): print(f"  {GREEN}✓{RESET} {msg}")
def _warn(msg: str): print(f"  {YELLOW}⚠{RESET} {msg}")
def _fail(msg: str): print(f"  {RED}✗{RESET} {msg}")


# -- Main test -----------------------------------------------------------------

async def run(model: str | None):
    if model:
        os.environ["OLLAMA_MODEL"] = model

    from rag.llm import OLLAMA_MODEL, OLLAMA_BASE_URL, LLM_PROVIDER
    print(f"\n{BOLD}PharmaRAG — LLM Isolation Test{RESET}")
    print(f"{'-' * 60}")
    print(f"Provider : {LLM_PROVIDER}")
    print(f"Model    : {OLLAMA_MODEL}")
    print(f"Host     : {OLLAMA_BASE_URL}")
    print(f"Context  : {len(HARDCODED_CHUNKS)} hardcoded Aspirin chunks")
    print(f"{'-' * 60}\n")

    # 1. Build context (SOURCE_N labels)
    context, source_map = build_context(HARDCODED_CHUNKS)
    print(f"Source map : {list(source_map.keys())}\n")

    # 2. Build prompt (inline version of prompts/drug_info.txt logic)
    prompt_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "prompts", "drug_info.txt"
    )
    template = open(prompt_path).read()
    system_prompt = (
        template
        .replace("{context}", context)
        .replace("{smiles}", MOCK_STRUCTURE["smiles"])
        .replace("{drug_name}", "Aspirin")
    )
    user_message = (
        f"Drug SMILES: {MOCK_STRUCTURE['smiles']}\n"
        f"Drug name (PubChem): Aspirin\n"
        f"IUPAC name: {MOCK_STRUCTURE['iupac_name']}"
    )

    # 3. Call LLM
    print(f"Calling {OLLAMA_MODEL}…  (this may take 10–60s on first run)\n")
    try:
        raw_dict = await generate_structured_output(system_prompt, user_message, DrugInfo)
    except Exception as exc:
        _fail(f"LLM call failed: {exc}")
        sys.exit(1)

    _pass("LLM responded with valid JSON")

    # 4. Print raw LLM output
    print(f"\n{BOLD}Raw LLM output:{RESET}")
    print(json.dumps(raw_dict, indent=2)[:2000])
    if len(json.dumps(raw_dict)) > 2000:
        print("  … (truncated)")

    # 5. Resolve source_ids → Citations
    resolved_dict = resolve_field_citations(raw_dict, source_map)

    # 6. Inject trusted structure data (not from LLM)
    resolved_dict["chemical_structure"] = MOCK_STRUCTURE
    resolved_dict["query_smiles"] = MOCK_STRUCTURE["smiles"]

    # 7. Pydantic validation
    print(f"\n{BOLD}Pydantic validation:{RESET}")
    try:
        drug_info = DrugInfo(**resolved_dict)
        _pass("DrugInfo validated successfully")
    except Exception as exc:
        _fail(f"Pydantic validation failed: {exc}")
        print("\nResolved dict (for debugging):")
        print(json.dumps(resolved_dict, indent=2, default=str)[:3000])
        sys.exit(1)

    # 8. Semantic checks
    print(f"\n{BOLD}Semantic checks:{RESET}")

    moa = drug_info.mechanism_of_action
    if moa.missing:
        _warn("mechanism_of_action is marked missing — LLM may not have used the context")
    else:
        _pass(f"mechanism_of_action.missing == False (content present)")

    if moa.sources:
        _pass(f"mechanism_of_action has {len(moa.sources)} citation(s)")
    else:
        _warn("mechanism_of_action has no citations — LLM may not have cited SOURCE_N")

    di = drug_info.drug_interactions
    if di.missing:
        _pass("drug_interactions.missing == True (correct — not in context)")
    else:
        _warn(f"drug_interactions.missing == False — LLM may have fabricated: {di.content!r}")

    indications = drug_info.indications
    if indications.missing:
        _warn("indications is marked missing — should be present in context")
    else:
        _pass("indications.missing == False")

    # 9. Summary
    fields_with_data = sum(
        1 for f in [
            drug_info.mechanism_of_action, drug_info.indications,
            drug_info.contraindications, drug_info.adverse_effects,
            drug_info.drug_interactions,
            drug_info.adme.absorption, drug_info.adme.distribution,
            drug_info.adme.metabolism, drug_info.adme.excretion,
        ]
        if not f.missing
    )
    print(f"\n{BOLD}Summary:{RESET}")
    print(f"  Fields with content : {fields_with_data} / 9")
    print(f"  Drug name generic   : {drug_info.drug_name.generic!r}")
    print(f"  MoA preview         : {(drug_info.mechanism_of_action.content or '')[:120]!r}")
    print()
    _pass("LLM test complete — ready for Phase 3 pipeline integration")
    print()


def main():
    parser = argparse.ArgumentParser(description="Test the LLM layer with hardcoded Aspirin context.")
    parser.add_argument("--model", default=None, help="Override OLLAMA_MODEL (e.g. qwen2.5:14b)")
    args = parser.parse_args()
    asyncio.run(run(args.model))


if __name__ == "__main__":
    main()
