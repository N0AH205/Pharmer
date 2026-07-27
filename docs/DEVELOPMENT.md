# PharmaRAG — Developer Documentation

> **Scope**: Tech stack rationale + complete guides for Phase 2 (Knowledge Base) and Phase 3 (RAG Pipeline).  
> This document is the single source of truth for continuing development after Phase 1.

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Tech Stack — Every Choice Explained](#2-tech-stack--every-choice-explained)
   - [Frontend: Next.js 15](#21-frontend-nextjs-15)
   - [Styling: Vanilla CSS + CSS Modules](#22-styling-vanilla-css--css-modules)
   - [Backend: Python FastAPI](#23-backend-python-fastapi)
   - [LLM: Qwen via Ollama (provider-agnostic)](#24-llm-qwen-via-ollama)
   - [Vector Database: ChromaDB](#25-vector-database-chromadb)
   - [Embeddings](#26-embeddings)
   - [Data Sources: PubChem, DailyMed, PubMed](#27-data-sources)
   - [Schema Enforcement: Pydantic](#28-schema-enforcement-pydantic)
3. [Architecture Deep-Dive](#3-architecture-deep-dive)
4. [Phase 2 — Knowledge Base Construction](#4-phase-2--knowledge-base-construction)
5. [Phase 3 — Live RAG Pipeline](#5-phase-3--live-rag-pipeline)
6. [Environment Variables Reference](#6-environment-variables-reference)
7. [File-by-File Reference](#7-file-by-file-reference)

---

## 1. Project Overview

PharmaRAG is a **Retrieval-Augmented Generation (RAG)** system — not a model trained from scratch.

```
User SMILES query
      |
[ Frontend: Next.js ]
      | HTTP POST /query
[ Backend: FastAPI ]
      |
[ Retriever: ChromaDB ]  <-- pharmaceutical text chunks (DailyMed, PubMed, PubChem)
      | relevant chunks
[ LLM: Qwen (Ollama) ]  <-- system prompt: "fill schema, cite sources, never fabricate"
      | structured JSON
[ Pydantic schema validation ]
      |
[ Frontend: DrugInfoCard ]  <-- tabbed UI with citations and missing-data flags
```

**Key principle**: The LLM never answers from its training knowledge. It only summarises
text chunks retrieved from curated pharmaceutical databases. Every claim is cited.
Missing data is flagged explicitly — never fabricated.

---

## 2. Tech Stack — Every Choice Explained

### 2.1 Frontend: Next.js 15

**What it is**: React framework with server-side rendering, App Router, and built-in API routes.

**Why Next.js over plain React or Vite?**

| Concern | Plain React/Vite | Next.js (chosen) |
|---|---|---|
| API proxy to Python backend | Needs separate Express server or CORS config | Built-in API Routes — `/app/api/query/route.ts` acts as a BFF (Backend for Frontend) |
| Image optimisation | Manual config | `next/image` with domain allowlist (PubChem PNG serving) |
| TypeScript | Needs manual config | Zero-config TypeScript |
| SEO / meta tags | Manual | `export const metadata` in `layout.tsx` |

**Why the API Route pattern matters:**
The frontend never calls the Python backend directly — it calls `/api/query`, a Next.js server function.
This means:
- The Python backend URL is never exposed to the browser
- Adding auth (API key, session) later happens in one place
- Phase 1 (mock) runs without the Python server at all

**Key files:**
```
frontend/app/
├── layout.tsx           <- Root HTML, SEO metadata
├── page.tsx             <- Main UI
├── globals.css          <- Design system
└── api/query/route.ts   <- The bridge between browser and Python backend
```

---

### 2.2 Styling: Vanilla CSS + CSS Modules

**What it is**: Plain CSS with scoped CSS Modules (`.module.css` per component). No Tailwind, no styled-components.

**Why?**
- **CSS Modules** give component-level scoping with zero runtime overhead. Class names like `.header`
  in `DrugInfoCard.module.css` cannot clash with `.header` in `SMILESInput.module.css`.
- **Design tokens** in `globals.css` (CSS custom properties like `--accent-primary`, `--bg-surface`)
  create a consistent system without a framework dependency.
- **Full control** over animations, glassmorphism, and grid backgrounds that are awkward in utility classes.

**Token system in `globals.css`:**
```css
:root {
  --bg-base: #070b14;           /* deepest background */
  --accent-primary: #00d4aa;    /* teal — all interactive accents */
  --accent-secondary: #6366f1;  /* indigo — user SMILES bubbles */
  --color-missing: #f59e0b;     /* amber — "data unavailable" state */
}
```
To change the entire colour scheme: edit ~10 lines in `globals.css`. Every component reads tokens.

---

### 2.3 Backend: Python FastAPI

**What it is**: Async Python web framework. Handles the RAG pipeline — retrieval, LLM calls, schema validation.

**Why Python over Node.js for the backend?**

| Ecosystem need | Node.js | Python (chosen) |
|---|---|---|
| ChromaDB client | JS client (less mature) | Native Python client (official) |
| LangChain / LlamaIndex | Available | Natively designed for Python |
| RDKit (SMILES parsing, Phase 3+) | No port | First-class Python library |
| Ollama client | Available | `ollama` package + HTTPx both work |
| Pydantic schema validation | Zod equivalent | Built into FastAPI natively |
| Scientific / ML ecosystem | Limited | NumPy, HuggingFace — Python-first |

**Why FastAPI over Flask or Django?**
- **Async by default** — critical for concurrent LLM API calls without blocking other requests
- **Pydantic integration** — request/response schemas automatically validated and serialised
- **Auto-generated docs** — visit `http://localhost:8000/docs` to test endpoints interactively
- **Minimal boilerplate** — a full RAG endpoint is ~20 lines

**Key files:**
```
backend/
├── main.py               <- FastAPI app, CORS, route definitions
├── rag/
│   ├── schema.py         <- Pydantic models (DrugInfo, FieldValue, etc.)
│   ├── pipeline.py       <- Orchestrates retrieval -> LLM -> validation
│   ├── retriever.py      <- ChromaDB vector search
│   └── llm.py            <- LLM provider client (Ollama/OpenAI/Anthropic)
└── ingest/
    ├── pubchem.py        <- Live PubChem REST API
    ├── dailymed.py       <- Phase 2 stub
    └── pubmed.py         <- Phase 2 stub
```

---

### 2.4 LLM: Qwen via Ollama

**What it is**: Qwen is Alibaba's open-source LLM family. Ollama is a local LLM runtime — think Docker, but for language models.

**Why Qwen?**
- **Free** — no API cost, no per-token billing
- **Local** — data never leaves your machine (important for pharmaceutical content)
- **Capable** — Qwen2.5-72B scores competitively with GPT-4o on structured reasoning tasks
- **JSON mode** — Ollama supports `"format": "json"` parameter for structured output
- **Switchable** — the `llm.py` provider pattern means you can swap to OpenAI/Anthropic with
  one environment variable change if Qwen underperforms on a specific task

**Qwen model selection guide:**

| Model | VRAM needed | Use case |
|---|---|---|
| `qwen2.5:7b` | ~6 GB | Development / testing on consumer GPU |
| `qwen2.5:14b` | ~10 GB | Better quality, still fast |
| `qwen2.5:72b` | ~48 GB | Full quality |
| `qwen2.5:72b-instruct-q4_K_M` | ~24 GB | Recommended for 24 GB GPU |

**Provider switching** — in `backend/rag/llm.py`:
```python
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama")
# Dispatches to _call_ollama() / _call_openai() / _call_anthropic()
# Change one line in backend/.env to switch the entire LLM backend
```

---

### 2.5 Vector Database: ChromaDB

**What it is**: Open-source, embeddable vector database. Stores text chunks as numerical vectors
(embeddings) and retrieves the most semantically similar ones given a query.

**Why ChromaDB over alternatives?**

| Option | Why not chosen |
|---|---|
| Pinecone | Paid cloud service; data leaves your machine |
| Weaviate | Heavier infrastructure — Docker required |
| FAISS | Fast but no metadata filtering, no built-in persistence |
| pgvector | Requires PostgreSQL; overkill for this scale |
| **ChromaDB** (chosen) | Pure Python, runs in-process, persists to disk, free, metadata filtering |

**How it works in this project:**
```
Ingestion (Phase 2):
  Drug text chunk -> embedding model -> 1536-dim vector -> stored in ChromaDB

Retrieval (Phase 3):
  Drug name query -> embed -> cosine similarity search -> top-8 chunks returned
```

ChromaDB persists to `data/chroma/` — this folder is gitignored. Each developer builds
their own local knowledge base from the same public source APIs.

---

### 2.6 Embeddings

**What it is**: Converting text to a high-dimensional vector so semantically similar texts are
geometrically close in vector space.

**Recommended: `text-embedding-3-small` (OpenAI)**

| Option | Dimensions | Cost | Notes |
|---|---|---|---|
| `text-embedding-3-small` | 1536 | $0.02/1M tokens | Very cheap; excellent for RAG |
| `text-embedding-3-large` | 3072 | $0.13/1M tokens | Better quality |
| `nomic-embed-text` (Ollama) | 768 | Free | Fully local; slightly lower quality |
| `mxbai-embed-large` (Ollama) | 1024 | Free | Good local alternative |

**For fully offline operation (no OpenAI key):**
```bash
ollama pull nomic-embed-text
```
Set `EMBEDDING_PROVIDER=ollama` in `backend/.env` (Phase 2 adds this config).

The pharmaceutical corpus for Phase 2 benchmark set (5-10 drugs) is not large — total embedding
cost with OpenAI is < $0.01.

---

### 2.7 Data Sources

#### PubChem — Active (Phase 1+)
- **URL**: https://pubchem.ncbi.nlm.nih.gov
- **Auth**: None required. Rate limit: 5 requests/second.
- **Scale**: 120M+ compounds.
- **Used for**: SMILES -> CID resolution, structure images, IUPAC name, molecular formula/weight,
  InChI, pharmacology text summaries.
- **Key API endpoints:**
  ```
  GET /compound/smiles/{smiles}/property/{fields}/JSON  -> compound properties
  GET /compound/CID/{cid}/PNG                           -> structure image
  GET /compound/CID/{cid}/description/JSON              -> pharmacology text
  ```

#### DailyMed / FDA — Phase 2
- **URL**: https://dailymed.nlm.nih.gov
- **Auth**: None required.
- **Scale**: 150k+ FDA-approved drug labels (Structured Product Labeling format).
- **Used for**: Indications, contraindications, adverse effects, drug interactions, clinical
  pharmacology (ADME). These are the legally authoritative descriptions — primary source for
  all clinical fields.
- **Key API endpoints:**
  ```
  GET /services/v2/spls.json?drug_name={name}   -> search labels by drug name
  GET /services/v2/spls/{set_id}.json            -> full label with named sections
  ```

#### PubMed — Phase 2
- **URL**: https://pubmed.ncbi.nlm.nih.gov
- **Auth**: Optional NCBI API key raises rate limit from 3 to 10 req/s (free registration).
- **Scale**: 38M+ citations with abstracts.
- **Used for**: Mechanistic detail for MoA, pharmacokinetic studies for ADME, research-level
  drug interaction data — enriches what FDA labels provide.
- **Key API endpoints (NCBI E-utilities):**
  ```
  GET /esearch.fcgi?db=pubmed&term={query}&retmax=N   -> search, returns PMIDs
  GET /efetch.fcgi?db=pubmed&id={pmids}&retmode=xml   -> fetch abstracts as XML
  ```

#### DrugBank — Requires License
- **URL**: https://www.drugbank.ca
- **Auth**: Free academic license available; commercial use is paid.
- **Used for**: Highly structured MoA, complete ADME data, comprehensive drug interaction database.
- **Status**: Stub in place. Integrate when license is confirmed.

---

### 2.8 Schema Enforcement: Pydantic

**What it is**: Python data validation library. Defines the `DrugInfo` model every LLM response must conform to.

**Why schema enforcement matters:**
Without it, the LLM might:
- Return a response missing the `drug_interactions` key — frontend crash
- Invent plausible-sounding but false ADME data — silent hallucination
- Return a number as a string — subtle type bugs

With Pydantic, every LLM response is validated before the API returns:
```python
# If LLM returns malformed JSON -> Pydantic raises ValidationError -> API returns 500
# The frontend never receives invalid data
drug_info = DrugInfo(**llm_response_dict)
```

**The `missing: true` pattern** — the most important anti-hallucination design decision:
```python
class FieldValue(BaseModel):
    content: Optional[str] = None   # None = no data available
    sources: list[Citation] = []    # always cite — even "missing" fields have no sources
    missing: bool = False           # True = "data not found", NOT a fabrication
```
The system prompt (`prompts/drug_info.txt`) explicitly tells the LLM:
> "If data is not present in the provided context, set `missing: true` and `content: null`.
> Do NOT approximate, infer, or fabricate."

---

## 3. Architecture Deep-Dive

### Request Flow (Phase 3 complete pipeline)

```
1. User enters SMILES in browser
2. Frontend: queryDrug(smiles) -> POST /api/query  [lib/api.ts]
3. Next.js API route (route.ts):
   - Validates request body
   - Proxies: POST http://localhost:8000/query
4. FastAPI (main.py):
   - Receives QueryRequest { smiles }
   - Calls run_pipeline(smiles)
5. pipeline.py:
   a. pubchem.enrich_structure(smiles)
      -> CID, IUPAC name, image URL, formula, weight
   b. retriever.retrieve(iupac_name, n=8)
      -> top-8 text chunks from ChromaDB
   c. Build prompt: system_prompt + context chunks + SMILES
   d. llm.generate_structured_output(prompt)
      -> raw JSON string from Qwen
   e. json.loads(raw) -> DrugInfo(**parsed) -> Pydantic validation
6. FastAPI returns { success: true, data: DrugInfo }
7. Next.js route returns JSON to browser
8. Frontend: appends assistant message with drugInfo
9. ChatInterface renders DrugInfoCard with all tabs populated
```

### Three-Layer Anti-Hallucination Stack

| Layer | Mechanism |
|---|---|
| **Retrieval** | LLM only sees retrieved chunks, not its general training knowledge |
| **System prompt** | Explicit instruction: "answer ONLY from context; use missing:true if absent" |
| **Schema validation** | Pydantic rejects any response not conforming to DrugInfo shape |

---

## 4. Phase 2 — Knowledge Base Construction

**Goal**: Ingest pharmaceutical text from DailyMed, PubMed, and PubChem into ChromaDB
so Phase 3 retrieval has real data.

**Estimated time**: 1-2 days for benchmark set (5-10 drugs).

---

### Step 1 — Install Phase 2 Dependencies

Uncomment the Phase 2 packages in `backend/requirements.txt`:

```
chromadb==0.5.3
openai==1.35.7
```

Install:
```bash
cd backend
pip install chromadb openai
```

For fully local embeddings (no OpenAI key needed):
```bash
pip install chromadb
ollama pull nomic-embed-text
```

---

### Step 2 — Implement `ingest/dailymed.py`

Replace the stub body with:

```python
import httpx

BASE_URL = "https://dailymed.nlm.nih.gov/dailymed/services/v2"

async def search_drug_labels(drug_name: str) -> list[dict]:
    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.get(
            f"{BASE_URL}/spls.json",
            params={"drug_name": drug_name, "pagesize": 5},
        )
        return resp.json().get("data", [])

async def get_label_sections(set_id: str) -> dict:
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(f"{BASE_URL}/spls/{set_id}.json")
        data = resp.json()

    sections = {}
    for section in data.get("data", {}).get("sections", []):
        name = section.get("name", "").lower()
        text = section.get("text", "")
        if "indication" in name:
            sections["indications"] = text
        elif "contraindication" in name:
            sections["contraindications"] = text
        elif "adverse" in name or "side effect" in name:
            sections["adverse_effects"] = text
        elif "drug interaction" in name:
            sections["drug_interactions"] = text
        elif "clinical pharmacology" in name:
            sections["clinical_pharmacology"] = text   # contains ADME
    return sections
```

---

### Step 3 — Implement `ingest/pubmed.py`

Replace the stub body with:

```python
import os, httpx
import xml.etree.ElementTree as ET

NCBI_API_KEY = os.getenv("NCBI_API_KEY", "")
BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

async def search_pubmed(query: str, max_results: int = 20) -> list[str]:
    params = {
        "db": "pubmed", "term": query, "retmax": max_results,
        "retmode": "json", "api_key": NCBI_API_KEY,
    }
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(f"{BASE_URL}/esearch.fcgi", params=params)
    return resp.json()["esearchresult"]["idlist"]

async def fetch_abstracts(pmids: list[str]) -> list[dict]:
    if not pmids:
        return []
    params = {
        "db": "pubmed", "id": ",".join(pmids),
        "retmode": "xml", "rettype": "abstract",
        "api_key": NCBI_API_KEY,
    }
    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.get(f"{BASE_URL}/efetch.fcgi", params=params)

    root = ET.fromstring(resp.text)
    results = []
    for article in root.findall(".//PubmedArticle"):
        pmid = article.findtext(".//PMID")
        title = article.findtext(".//ArticleTitle")
        abstract = article.findtext(".//AbstractText")
        results.append({"pmid": pmid, "title": title, "abstract": abstract or ""})
    return results
```

---

### Step 4 — Create the Ingestion Script

Create `backend/ingest/run_ingest.py`:

```python
"""
Populate ChromaDB with drug data for the benchmark set.

Run once before Phase 3:
    cd backend
    python -m ingest.run_ingest
"""

import asyncio
import chromadb
from openai import AsyncOpenAI

from ingest.pubchem import get_pharmacology_text, get_compound_by_smiles
from ingest.dailymed import search_drug_labels, get_label_sections
from ingest.pubmed import search_pubmed, fetch_abstracts

CHROMA_PATH = "../data/chroma"
COLLECTION_NAME = "pharma_docs"

# Start with these — expand for Phase 4 evaluation
BENCHMARK_DRUGS = [
    {"name": "Aspirin",      "smiles": "CC(=O)Oc1ccccc1C(=O)O"},
    {"name": "Ibuprofen",    "smiles": "CC(C)Cc1ccc(cc1)C(C)C(=O)O"},
    {"name": "Metformin",    "smiles": "CN(C)C(=N)NC(N)=N"},
    {"name": "Atorvastatin", "smiles": "CC(C)c1c(C(=O)Nc2ccccc2F)c(-c2ccccc2)c(-c2ccc(F)cc2)n1CCC(O)CC(O)CC(=O)O"},
    {"name": "Caffeine",     "smiles": "Cn1cnc2c1c(=O)n(c(=O)n2C)C"},
]

async def embed_text(text: str, client: AsyncOpenAI) -> list[float]:
    resp = await client.embeddings.create(
        model="text-embedding-3-small",
        input=text[:8000],
    )
    return resp.data[0].embedding

async def ingest_drug(drug: dict, collection, openai_client: AsyncOpenAI):
    name = drug["name"]
    smiles = drug["smiles"]
    print(f"\n-- Ingesting {name} --")
    chunks = []

    # PubChem pharmacology text
    props = await get_compound_by_smiles(smiles)
    if props:
        cid = props.get("CID")
        text = await get_pharmacology_text(cid)
        if text:
            chunks.append({
                "text": text, "source": f"PubChem CID {cid}",
                "url": f"https://pubchem.ncbi.nlm.nih.gov/compound/{cid}",
                "drug": name, "field": "pharmacology",
            })
            print(f"  PubChem OK ({len(text)} chars)")

    # DailyMed sections
    labels = await search_drug_labels(name)
    if labels:
        set_id = labels[0].get("setid")
        sections = await get_label_sections(set_id)
        for field, text in sections.items():
            if text:
                chunks.append({
                    "text": text[:4000], "source": f"DailyMed SPL -- {name}",
                    "url": "https://dailymed.nlm.nih.gov",
                    "drug": name, "field": field,
                })
        print(f"  DailyMed OK ({len(sections)} sections)")

    # PubMed abstracts
    pmids = await search_pubmed(f"{name} pharmacology mechanism", max_results=10)
    abstracts = await fetch_abstracts(pmids)
    for ab in abstracts:
        if ab["abstract"]:
            chunks.append({
                "text": f"{ab['title']}\n\n{ab['abstract']}",
                "source": f"PubMed PMID {ab['pmid']}",
                "url": f"https://pubmed.ncbi.nlm.nih.gov/{ab['pmid']}",
                "drug": name, "field": "research",
            })
    print(f"  PubMed OK ({len(abstracts)} abstracts)")

    # Embed and store
    for i, chunk in enumerate(chunks):
        embedding = await embed_text(chunk["text"], openai_client)
        collection.add(
            ids=[f"{name}-{i}"],
            embeddings=[embedding],
            documents=[chunk["text"]],
            metadatas=[{k: v for k, v in chunk.items() if k != "text"}],
        )
    print(f"  Stored {len(chunks)} chunks")

async def main():
    db = chromadb.PersistentClient(path=CHROMA_PATH)
    collection = db.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )
    openai_client = AsyncOpenAI()

    for drug in BENCHMARK_DRUGS:
        await ingest_drug(drug, collection, openai_client)

    print(f"\nDone. Total chunks: {collection.count()}")

if __name__ == "__main__":
    asyncio.run(main())
```

**Run it:**
```bash
cd backend
python -m ingest.run_ingest
```

---

### Step 5 — Implement `rag/retriever.py`

Replace the stub with:

```python
import os, chromadb
from openai import AsyncOpenAI

CHROMA_PATH = os.getenv("CHROMA_PATH", "../data/chroma")
COLLECTION_NAME = "pharma_docs"

class Retriever:
    def __init__(self):
        self.db = chromadb.PersistentClient(path=CHROMA_PATH)
        self.collection = self.db.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
        self._ready = self.collection.count() > 0

    def is_ready(self) -> bool:
        return self._ready

    async def retrieve(self, query: str, n_results: int = 8) -> list[dict]:
        client = AsyncOpenAI()
        resp = await client.embeddings.create(
            model="text-embedding-3-small", input=query
        )
        query_vec = resp.data[0].embedding

        results = self.collection.query(
            query_embeddings=[query_vec],
            n_results=n_results,
            include=["documents", "metadatas", "distances"],
        )
        return [
            {
                "text": doc, "source": meta["source"],
                "url": meta.get("url"), "field": meta.get("field"),
                "distance": dist,
            }
            for doc, meta, dist in zip(
                results["documents"][0],
                results["metadatas"][0],
                results["distances"][0],
            )
        ]
```

---

## 5. Phase 3 — Live RAG Pipeline

**Goal**: Wire retrieval + Qwen + schema validation into a live API response.

**Prerequisites**:
- Phase 2 complete (ChromaDB populated with data)
- Ollama installed and running

---

### Step 1 — Install Ollama + Qwen

1. Download Ollama: https://ollama.com/download
2. Pull a Qwen model:
```bash
ollama pull qwen2.5:7b        # fast, low VRAM (development)
ollama pull qwen2.5:14b       # better quality
ollama pull qwen2.5:72b-instruct-q4_K_M  # recommended for production
```
3. Verify it's running:
```bash
curl http://localhost:11434/api/tags
```

---

### Step 2 — Implement `rag/llm.py` — Ollama Branch

Replace the `_call_ollama` stub body:

```python
async def _call_ollama(system_prompt, user_message, schema) -> dict:
    import httpx, json

    payload = {
        "model": OLLAMA_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_message},
        ],
        "format": "json",      # forces JSON-only output from Ollama
        "stream": False,
        "options": {
            "temperature": 0.1,    # low temperature = factual, deterministic
            "num_predict": 4096,
        },
    }

    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(f"{OLLAMA_BASE_URL}/api/chat", json=payload)
        resp.raise_for_status()

    raw = resp.json()["message"]["content"]
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"LLM returned invalid JSON: {e}\nRaw: {raw[:500]}")
```

---

### Step 3 — Update `rag/pipeline.py`

Replace the `run_pipeline` stub:

```python
import json
from pathlib import Path

from rag.schema import DrugInfo
from rag.retriever import Retriever
from rag.llm import generate_structured_output
from ingest.pubchem import enrich_structure

PROMPT_TEMPLATE = Path(__file__).parent.parent / "prompts" / "drug_info.txt"
_retriever = None

def get_retriever() -> Retriever:
    global _retriever
    if _retriever is None:
        _retriever = Retriever()
    return _retriever

async def run_pipeline(smiles: str) -> DrugInfo:
    retriever = get_retriever()

    # 1. Resolve SMILES via PubChem
    structure_data = await enrich_structure(smiles)
    drug_query = structure_data.get("iupac_name") or smiles

    # 2. Retrieve relevant chunks
    chunks = await retriever.retrieve(drug_query, n_results=8)
    context = "\n\n---\n\n".join(
        f"[Source {i}: {c['source']}]\n{c['text']}"
        for i, c in enumerate(chunks, 1)
    )

    # 3. Build prompt
    template = PROMPT_TEMPLATE.read_text()
    system_prompt = template.replace("{context}", context).replace("{smiles}", smiles)
    user_message = f"Drug SMILES: {smiles}\nIUPAC name (PubChem): {drug_query}"

    # 4. Call LLM
    raw_dict = await generate_structured_output(
        system_prompt=system_prompt,
        user_message=user_message,
        output_schema=DrugInfo,
    )

    # 5. Inject trusted PubChem structure (not from LLM)
    raw_dict["chemical_structure"] = structure_data
    raw_dict["query_smiles"] = smiles

    # 6. Validate
    return DrugInfo(**raw_dict)
```

---

### Step 4 — Swap the Mock API Route for a Real Proxy

In `frontend/app/api/query/route.ts`, replace the mock block with:

```typescript
export async function POST(req: NextRequest) {
  const body = await req.json().catch(() => null);
  if (!body?.smiles) {
    return NextResponse.json({ success: false, error: "Missing smiles" }, { status: 400 });
  }

  const backendRes = await fetch("http://localhost:8000/query", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ smiles: body.smiles }),
  });

  const data = await backendRes.json();
  return NextResponse.json(data, { status: backendRes.status });
}
```

---

### Step 5 — Start Both Servers

```bash
# Terminal 1 — Python backend
cd backend
uvicorn main:app --reload --port 8000

# Terminal 2 — Next.js frontend
cd frontend
npm run dev
```

Navigate to `http://localhost:3000`, enter Aspirin SMILES:
```
CC(=O)Oc1ccccc1C(=O)O
```

---

### Phase 3 Debugging Guide

| Symptom | Cause | Fix |
|---|---|---|
| LLM returns invalid JSON | Temperature too high / model too small | Lower `temperature` to 0.05; try a larger model |
| ChromaDB returns 0 results | Ingestion not run, or query mismatch | Run `run_ingest.py`; always query by IUPAC name, not SMILES |
| Pydantic ValidationError | LLM returned bare string instead of FieldValue | Add recovery: wrap bare strings as `{"content": str, "sources": [], "missing": false}` |
| Ollama timeout | Model loading slow on first call | Increase FastAPI client timeout to 180s; pre-warm Ollama |
| All fields `missing: true` | Retriever found no relevant chunks | Check chunk count in ChromaDB; adjust `n_results` |

---

## 6. Environment Variables Reference

All variables go in `backend/.env` (copy from `backend/.env.example`).

| Variable | Default | Required | Description |
|---|---|---|---|
| `LLM_PROVIDER` | `ollama` | Yes | `ollama` / `openai` / `anthropic` |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | If ollama | Ollama server URL |
| `OLLAMA_MODEL` | `qwen2.5:72b` | If ollama | Any model pulled via Ollama |
| `OPENAI_API_KEY` | — | If openai | sk-... |
| `OPENAI_MODEL` | `gpt-4o` | If openai | OpenAI model name |
| `ANTHROPIC_API_KEY` | — | If anthropic | sk-ant-... |
| `ANTHROPIC_MODEL` | `claude-3-5-sonnet-20241022` | If anthropic | Anthropic model name |
| `NCBI_API_KEY` | — | No | Raises PubMed rate limit 3->10 req/s. Free at ncbi.nlm.nih.gov/account |
| `CHROMA_PATH` | `../data/chroma` | Phase 2+ | Path to ChromaDB persistence directory |

---

## 7. File-by-File Reference

### Frontend

| File | Role | Next edit in Phase |
|---|---|---|
| `app/page.tsx` | Layout + chat state management | 2 (add loading skeleton) |
| `app/globals.css` | Design tokens + global styles | Any (visual changes) |
| `app/layout.tsx` | HTML root, SEO metadata | Any |
| `app/api/query/route.ts` | **Phase 1**: mock. **Phase 3**: real proxy | 3 |
| `lib/types.ts` | TypeScript DrugInfo schema | Only if schema fields change |
| `lib/api.ts` | Frontend fetch wrapper | Only if API changes |
| `components/DrugInfoCard.tsx` | Tabbed drug info card | Add tabs for new schema fields |
| `components/SMILESInput.tsx` | Input + example chips | Any |
| `components/FieldBlock.tsx` | Collapsible field + missing-data state | Only if UX changes |
| `components/StructureViewer.tsx` | PubChem structure image + properties | Only if fields change |
| `components/CitationBadge.tsx` | Source citation chips | Only if citation format changes |
| `components/ChatInterface.tsx` | Chat thread + empty state | Phase 3 (add follow-up query) |

### Backend

| File | Role | Next edit in Phase |
|---|---|---|
| `main.py` | FastAPI app, routes, CORS | 3 (add retriever health check) |
| `rag/schema.py` | Pydantic DrugInfo model | Only if output schema changes |
| `rag/pipeline.py` | **Phase 1**: mock. **Phase 3**: full RAG | 3 |
| `rag/retriever.py` | ChromaDB vector search | 2 (implement), 3 (tune n_results) |
| `rag/llm.py` | LLM provider client | 3 (implement stubs) |
| `ingest/pubchem.py` | PubChem REST API | 2 (add text ingestion calls) |
| `ingest/dailymed.py` | DailyMed FDA labels | 2 (implement) |
| `ingest/pubmed.py` | PubMed abstracts | 2 (implement) |
| `ingest/run_ingest.py` | Ingestion script | Create in Phase 2 |
| `prompts/drug_info.txt` | LLM system prompt | 3 (tune for accuracy per field) |
| `.env.example` | Environment variable template | As new variables are added |

### Docs

| File | Primary audience |
|---|---|
| `docs/schema.md` | **Domain expert** — expected content + missing-data rules per field |
| `docs/data_sources.md` | **Both** — API references + ingestion strategy |
| `docs/DEVELOPMENT.md` | **Developer** — this document |
| `README.md` | **Anyone** — quick-start |
