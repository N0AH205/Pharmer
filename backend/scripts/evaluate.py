"""
RAG Pipeline Evaluation Script — Phase 4.

Queries the live RAG pipeline for all benchmark drugs, evaluates the results
against gold-standard reference data using schema, citation, keyword matching,
and LLM-assisted scoring, and saves a performance report.

Usage:
    cd backend
    .venv\\Scripts\\python -m scripts.evaluate
"""

import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import json
import asyncio
import httpx
from datetime import datetime
from pydantic import BaseModel, Field

# Ensure backend directory is in python path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from rag.pipeline import run_pipeline
from rag.schema import DrugInfo
from rag.llm import GEMINI_API_KEY, GEMINI_MODEL

# Console formatting
BOLD = "\033[1m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
CYAN = "\033[96m"
RESET = "\033[0m"

# Paths
GOLD_STANDARD_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "data",
    "gold_standard.json",
)
REPORT_OUT_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "data",
    "evaluation_report.json",
)


# Pydantic model for LLM-assisted evaluation schema
class EvalMetrics(BaseModel):
    correctness_score: int = Field(
        ...,
        description="Factual correctness and detail recall score (0 to 100) compared to the gold standard.",
    )
    hallucination_score: int = Field(
        ...,
        description="Score indicating presence of unsupported or fabricated facts (0 to 100, where 0 is perfect and 100 means highly hallucinated/fabricated).",
    )
    rationale: str = Field(
        ...,
        description="Explanation and specific observations supporting the scores.",
    )


async def call_llm_evaluator(
    drug_name: str, field_name: str, generated_text: str, gold_standard_text: str
) -> EvalMetrics:
    """Call Google Gemini to compare generated text against gold standard facts with backoff retry."""
    if not GEMINI_API_KEY:
        return EvalMetrics(
            correctness_score=0,
            hallucination_score=0,
            rationale="GEMINI_API_KEY env variable not set. LLM eval skipped.",
        )

    system_prompt = (
        "You are an expert pharmaceutical research auditor. Your task is to evaluate RAG-generated drug summaries "
        "against the gold-standard reference facts. You must output a JSON object containing correctness_score, "
        "hallucination_score, and a detailed rationale."
    )

    user_message = f"""
Drug: {drug_name}
Field: {field_name}

---
[GOLD STANDARD FACTS]
{gold_standard_text}

---
[GENERATED TEXT]
{generated_text}

---
Evaluation Rules:
1. Correctness Score (0-100): Measure how much of the gold standard clinical facts, values, or mechanisms were successfully captured. 100 means all facts are present.
2. Hallucination Score (0-100): Measure if the generated text adds clinical details, claims, values, or enzymes that are NOT listed or supported in the gold standard facts. 0 means no hallucinations/unsupported details.
3. Rationale: Briefly explain your scores.
"""

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": user_message}]
            }
        ],
        "systemInstruction": {
            "parts": [{"text": system_prompt}]
        },
        "generationConfig": {
            "responseMimeType": "application/json",
            "temperature": 0.1,
        }
    }

    max_retries = 5
    delay = 3.0
    for i in range(max_retries):
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(url, json=payload)
                if resp.status_code == 429:
                    raise httpx.HTTPStatusError("429 Too Many Requests", request=resp.request, response=resp)
                resp.raise_for_status()
                data = resp.json()
                raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
                parsed = json.loads(raw_text)
                await asyncio.sleep(1.0)
                return EvalMetrics(**parsed)
        except Exception as exc:
            if i < max_retries - 1:
                print(f"  {YELLOW}Rate limit or API error during {field_name} eval. Retrying in {delay:.1f}s...{RESET}")
                await asyncio.sleep(delay)
                delay *= 2
            else:
                return EvalMetrics(
                    correctness_score=0,
                    hallucination_score=0,
                    rationale=f"LLM Evaluator failed after {max_retries} attempts. Error: {exc}",
                )


def evaluate_field(
    drug_name: str,
    field_name: str,
    generated_content: str | None,
    is_missing: bool,
    expected_keywords: list[str],
) -> dict:
    """Evaluate a single field using keyword matching."""
    if is_missing or not generated_content:
        return {
            "keyword_score": 0.0,
            "matched_keywords": [],
            "missing_keywords": expected_keywords,
            "length": 0,
        }

    content_lower = generated_content.lower()
    matched = []
    missing = []

    for kw in expected_keywords:
        if kw.lower() in content_lower:
            matched.append(kw)
        else:
            missing.append(kw)

    keyword_score = (len(matched) / len(expected_keywords) * 100) if expected_keywords else 100.0

    return {
        "keyword_score": round(keyword_score, 1),
        "matched_keywords": matched,
        "missing_keywords": missing,
        "length": len(generated_content),
    }


async def evaluate_drug(drug_key: str, gold_data: dict, llm_eval_enabled: bool = False) -> dict:
    """Run pipeline and evaluate generated profile against gold standard reference."""
    smiles = gold_data["smiles"]
    print(f"Querying RAG pipeline for {BOLD}{drug_key.upper()}{RESET} ({smiles}) ...")

    start_time = datetime.now()
    max_retries = 5
    delay = 3.0
    res = None
    schema_compliance = 100
    for i in range(max_retries):
        try:
            res = await run_pipeline(smiles, debug=False)
            break
        except Exception as exc:
            if ("429" in str(exc) or "too many requests" in str(exc).lower()) and i < max_retries - 1:
                print(f"  {YELLOW}RAG query rate limited. Retrying in {delay:.1f}s...{RESET}")
                await asyncio.sleep(delay)
                delay *= 2
            else:
                print(f"  {RED}✗ RAG pipeline query failed: {exc}{RESET}")
                return {
                    "drug": drug_key,
                    "success": False,
                    "error": str(exc),
                    "schema_compliance": 0,
                    "overall_score": 0.0,
                }
    duration_sec = (datetime.now() - start_time).total_seconds()

    if res is None:
        print(f"  {RED}✗ RAG pipeline query failed: rate limit exceeded after {max_retries} attempts.{RESET}")
        return {
            "drug": drug_key,
            "success": False,
            "error": "Rate limit exceeded (429)",
            "schema_compliance": 0,
            "overall_score": 0.0,
        }

    # Gather fields to evaluate
    fields_to_evaluate = {
        "mechanism_of_action": {
            "gen": res.pharmacodynamics.mechanism_of_action.content,
            "missing": res.pharmacodynamics.mechanism_of_action.missing,
            "sources": res.pharmacodynamics.mechanism_of_action.sources,
            "gold": gold_data["mechanism_of_action"],
        },
        "indications": {
            "gen": res.therapeutic_profile.indications.content,
            "missing": res.therapeutic_profile.indications.missing,
            "sources": res.therapeutic_profile.indications.sources,
            "gold": gold_data["indications"],
        },
        "contraindications": {
            "gen": res.therapeutic_profile.contraindications.content,
            "missing": res.therapeutic_profile.contraindications.missing,
            "sources": res.therapeutic_profile.contraindications.sources,
            "gold": gold_data["contraindications"],
        },
        "absorption": {
            "gen": res.adme.absorption.content,
            "missing": res.adme.absorption.missing,
            "sources": res.adme.absorption.sources,
            "gold": gold_data["adme"]["absorption"],
        },
        "distribution": {
            "gen": res.adme.distribution.content,
            "missing": res.adme.distribution.missing,
            "sources": res.adme.distribution.sources,
            "gold": gold_data["adme"]["distribution"],
        },
        "metabolism": {
            "gen": res.adme.metabolism.content,
            "missing": res.adme.metabolism.missing,
            "sources": res.adme.metabolism.sources,
            "gold": gold_data["adme"]["metabolism"],
        },
        "excretion": {
            "gen": res.adme.excretion.content,
            "missing": res.adme.excretion.missing,
            "sources": res.adme.excretion.sources,
            "gold": gold_data["adme"]["excretion"],
        },
    }

    # Evaluate each field
    evaluated_fields = {}
    citation_checks = []

    for f_name, data in fields_to_evaluate.items():
        gen_text = data["gen"]
        is_missing = data["missing"]
        sources = data["sources"]
        gold_kws = data["gold"]

        # 1. Keyword check
        field_eval = evaluate_field(drug_key, f_name, gen_text, is_missing, gold_kws)

        # 2. Citation check
        if not is_missing and gen_text:
            has_sources = len(sources) > 0 and all(src.source and src.url for src in sources)
            citation_checks.append(100 if has_sources else 0)
        else:
            has_sources = True  # Missing fields don't need citations

        # 3. LLM evaluation check
        if llm_eval_enabled:
            gold_summary = ", ".join(gold_kws)
            llm_eval = await call_llm_evaluator(
                drug_key, f_name, gen_text or "Data unavailable / missing.", gold_summary
            )
            correctness = llm_eval.correctness_score
            hallucination = llm_eval.hallucination_score
            rationale = llm_eval.rationale
        else:
            correctness = 0
            hallucination = 0
            rationale = "LLM evaluation disabled (run with --llm-eval to enable)"

        field_eval.update({
            "has_sources": has_sources,
            "sources_count": len(sources),
            "correctness_score": correctness,
            "hallucination_score": hallucination,
            "rationale": rationale,
        })

        evaluated_fields[f_name] = field_eval

    citation_score = (sum(citation_checks) / len(citation_checks)) if citation_checks else 100.0

    # Calculate aggregate metrics
    kw_scores = [f["keyword_score"] for f in evaluated_fields.values()]
    avg_keyword_score = sum(kw_scores) / len(kw_scores) if kw_scores else 0.0

    corr_scores = [f["correctness_score"] for f in evaluated_fields.values()]
    avg_correctness_score = sum(corr_scores) / len(corr_scores) if corr_scores else 0.0

    hall_scores = [f["hallucination_score"] for f in evaluated_fields.values()]
    avg_hallucination_score = sum(hall_scores) / len(hall_scores) if hall_scores else 0.0

    # overall score
    if llm_eval_enabled:
        hallucination_penalty = avg_hallucination_score
        overall_score = (schema_compliance + citation_score + avg_correctness_score + (100.0 - hallucination_penalty)) / 4.0
    else:
        overall_score = (schema_compliance + citation_score + avg_keyword_score) / 3.0

    print(f"  {GREEN}+ Completed evaluation for {drug_key.upper()}{RESET}")
    print(f"    Keyword Recall: {avg_keyword_score:.1f}%")
    print(f"    Correctness:    {avg_correctness_score:.1f}%")
    print(f"    Hallucination:  {avg_hallucination_score:.1f}%")
    print(f"    Citation Rate:  {citation_score:.1f}%")

    return {
        "drug": drug_key,
        "success": True,
        "duration_sec": round(duration_sec, 2),
        "schema_compliance": schema_compliance,
        "citation_score": round(citation_score, 1),
        "avg_keyword_score": round(avg_keyword_score, 1),
        "avg_correctness_score": round(avg_correctness_score, 1),
        "avg_hallucination_score": round(avg_hallucination_score, 1),
        "overall_score": round(overall_score, 1),
        "fields": evaluated_fields,
    }


async def main():
    import argparse
    parser = argparse.ArgumentParser(description="PharmaRAG Evaluation Suite")
    parser.add_argument("--llm-eval", action="store_true", help="Enable LLM-assisted evaluation (correctness & hallucination auditing)")
    args = parser.parse_args()

    print("=" * 70)
    print(f"{BOLD}PharmaRAG — RAG Evaluation Suite (Phase 4){RESET}")
    print("=" * 70)

    # 1. Load gold standard
    if not os.path.exists(GOLD_STANDARD_PATH):
        print(f"{RED}Error: Gold standard profiles not found at {GOLD_STANDARD_PATH}{RESET}")
        sys.exit(1)

    with open(GOLD_STANDARD_PATH, "r", encoding="utf-8") as f:
        gold_standards = json.load(f)

    print(f"Loaded {len(gold_standards)} gold-standard drug profiles from database.\n")

    results = []
    for drug_key, gold_data in gold_standards.items():
        res = await evaluate_drug(drug_key, gold_data, llm_eval_enabled=args.llm_eval)
        results.append(res)
        print()
        await asyncio.sleep(20.0)
        print()

    # 2. Print table report
    print("\n" + "=" * 76)
    print(f"{BOLD}{'Drug':<15} {'Recall %':<10} {'Correct %':<10} {'Halluc %':<10} {'Citations %':<12} {'Overall %':<10}{RESET}")
    print("-" * 76)

    success_results = [r for r in results if r["success"]]
    for r in results:
        if r["success"]:
            drug_name = r["drug"].upper()
            kw = f"{r['avg_keyword_score']:.1f}%"
            corr = f"{r['avg_correctness_score']:.1f}%"
            hall = f"{r['avg_hallucination_score']:.1f}%"
            cit = f"{r['citation_score']:.1f}%"
            ovr = f"{r['overall_score']:.1f}%"
            print(f"{drug_name:<15} {kw:<10} {corr:<10} {hall:<10} {cit:<12} {ovr:<10}")
        else:
            print(f"{r['drug'].upper():<15} {RED}{'FAILED':<59}{RESET}")

    print("-" * 76)

    if success_results:
        avg_kw = sum(r["avg_keyword_score"] for r in success_results) / len(success_results)
        avg_corr = sum(r["avg_correctness_score"] for r in success_results) / len(success_results)
        avg_hall = sum(r["avg_hallucination_score"] for r in success_results) / len(success_results)
        avg_cit = sum(r["citation_score"] for r in success_results) / len(success_results)
        avg_ovr = sum(r["overall_score"] for r in success_results) / len(success_results)
        print(f"{BOLD}{'AVERAGE':<15} {avg_kw:.1f}%      {avg_corr:.1f}%      {avg_hall:.1f}%      {avg_cit:.1f}%        {avg_ovr:.1f}%{RESET}")
    print("=" * 76)

    # 3. Save report output
    report_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "model_evaluated": GEMINI_MODEL,
        "metrics_average": {
            "avg_keyword_score": round(avg_kw, 1) if success_results else 0,
            "avg_correctness_score": round(avg_corr, 1) if success_results else 0,
            "avg_hallucination_score": round(avg_hall, 1) if success_results else 0,
            "avg_citation_score": round(avg_cit, 1) if success_results else 0,
            "avg_overall_score": round(avg_ovr, 1) if success_results else 0,
        },
        "drugs_detail": results,
    }

    with open(REPORT_OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2)

    print(f"\nSaved full evaluation report to: {CYAN}{REPORT_OUT_PATH}{RESET}\n")


if __name__ == "__main__":
    asyncio.run(main())
