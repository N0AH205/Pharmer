# PharmaRAG — Developer Documentation

> **Scope**: Tech stack rationale + complete guides for Phase 2 (Knowledge Base) and Phase 3 (RAG Pipeline).  
> This document is the single source of truth for continuing development, reflecting the current active LLM configuration using the Google Gemini API.

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Tech Stack — Every Choice Explained](#2-tech-stack--every-choice-explained)
   - [Frontend: Next.js 15](#21-frontend-nextjs-15)
   - [Styling: Vanilla CSS + CSS Modules](#22-styling-vanilla-css--css-modules)
   - [Backend: Python FastAPI](#23-backend-python-fastapi)
   - [LLM: Google Gemini (provider-switchable)](#24-llm-google-gemini)
   - [Vector Database: ChromaDB](#25-vector-database-chromadb)
   - [Embeddings: Local nomic-embed-text via Ollama](#26-embeddings)
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
[ LLM: Google Gemini ]   <-- system prompt: "fill schema, cite sources, never fabricate"
      | structured JSON (application/json)
[ Pydantic schema validation ]
      |
[ Frontend: DrugInfoCard ]  <-- tabbed UI with citations and missing-data flags
```

**Key principle**: The LLM never answers from its training knowledge. It only summarises text chunks retrieved from curated pharmaceutical databases. Every claim is cited. Missing data is flagged explicitly — never fabricated.

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
The frontend never calls the Python backend directly — it calls `/api/query`, a Next.js server function. This means:
- The Python backend URL is never exposed to the browser.
- Adding authentication or rate-limiting later happens in one centralized location.
- Phase 1 (mock) runs without needing the Python server running at all.

**Key files:**
```
frontend/app/
├── layout.tsx           <- Root HTML, SEO metadata
├── page.tsx             <- Main UI
├── globals.css          <- Design system styling
└── api/query/route.ts   <- The bridge between browser and Python backend
```

---

### 2.2 Styling: Vanilla CSS + CSS Modules

**What it is**: Plain CSS with scoped CSS Modules (`.module.css` per component). No Tailwind, no styled-components.

**Why?**
- **CSS Modules** give component-level scoping with zero runtime overhead. Class names like `.header` in `DrugInfoCard.module.css` cannot clash with `.header` in `SMILESInput.module.css`.
- **Design tokens** in `globals.css` (CSS custom properties like `--accent-primary`, `--bg-surface`) create a consistent system without a framework dependency.
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
- **Async by default** — critical for concurrent LLM API calls without blocking other requests.
- **Pydantic integration** — request/response schemas automatically validated and serialised.
- **Auto-generated docs** — visit `http://localhost:8000/docs` to test endpoints interactively.
- **Minimal boilerplate** — a full RAG endpoint is ~20 lines.

**Key files:**
```
backend/
├── main.py               <- FastAPI app, CORS, route definitions
├── rag/
│   ├── schema.py         <- Pydantic models (DrugInfo, FieldValue, etc.)
│   ├── pipeline.py       <- Orchestrates retrieval -> LLM -> validation
│   ├── retriever.py      <- ChromaDB vector search
│   ├── context_builder.py<- Formats retrieved text for the LLM context
│   └── llm.py            <- LLM provider client (Gemini/Ollama/OpenAI/Anthropic)
└── ingest/
    ├── pubchem.py        <- Live PubChem REST API
    ├── dailymed.py       <- Ingests FDA DailyMed labels
    ├── pubmed.py         <- Ingests PubMed abstracts
    └── run_ingest.py     <- Main ingestion orchestration script
```

---

### 2.4 LLM: Google Gemini

**What it is**: Google's family of highly capable language models, accessed via the Gemini API using an API key.

**Why Google Gemini?**
- **Extremely Capable**: High reasoning performance for structured tasks like RAG, even with compact models like `gemini-3.5-flash-lite` or `gemini-1.5-flash`.
- **Native Structured JSON Mode**: Native support for schema enforcement (`responseMimeType: "application/json"`) ensures output matches our Pydantic schema perfectly.
- **Low Latency & Cost-Effective**: Quick response generation, and cost-effective API rates with generous free/low-cost tiers.
- **No Heavy SDKs**: We query the Gemini API directly using Python's `httpx` library, making the codebase lightweight and dependencies minimal.
- **Switchable**: The `llm.py` provider pattern allows switching to other providers (Ollama, OpenAI, Anthropic) simply by changing environment variables.

**Gemini Model Guide:**
Our primary recommended models for development and production are:
- `gemini-3.5-flash-lite`: Recommended for fast, low-cost structured RAG responses.
- `gemini-1.5-flash`: Highly optimized general-purpose model.
- `gemini-1.5-pro`: Deepest reasoning capabilities, useful for complex biomedical synthesis.

**Provider switching configuration** — in `backend/rag/llm.py`:
```python
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini")
# Dispatches to _call_gemini() / _call_ollama() / _call_openai() / _call_anthropic()
# Change LLM_PROVIDER in backend/.env to switch LLM backends
```

---

### 2.5 Vector Database: ChromaDB

**What it is**: Open-source, embeddable vector database. Stores text chunks as numerical vectors (embeddings) and retrieves the most semantically similar ones given a query.

**Why ChromaDB over alternatives?**

| Option | Why not chosen |
|---|---|
| Pinecone | Paid cloud service; data leaves your machine |
| Weaviate | Heavier infrastructure — Docker required |
| FAISS | Fast but no metadata filtering, no built-in persistence |
| pgvector | Requires PostgreSQL; overkill for this scale |
| **ChromaDB** (chosen) | Pure Python, runs in-process, persists to disk, free, metadata filtering |

**How it works in this project (Two-Stage Retrieval):**
1. **Stage 1 (Metadata Filter)**: Filter by `pubchem_cid` to ensure only text chunks corresponding to the queried chemical structure are searched. This guarantees 100% drug identity correctness.
2. **Stage 2 (Vector Similarity)**: Rank the filtered subset by cosine similarity against the query embedding.

ChromaDB persists to `data/chroma/` (gitignored). Each developer builds their own local knowledge base using the ingestion scripts.

---

### 2.6 Embeddings: Local nomic-embed-text via Ollama

**What it is**: Converting text to a high-dimensional vector so semantically similar texts are geometrically close in vector space.

**Default Configuration: Local `nomic-embed-text` via Ollama**
We use local embeddings by default to ensure no API costs are incurred during search and ingestion.

| Option | Dimensions | Provider | Cost | Notes |
|---|---|---|---|---|
| `nomic-embed-text` | 768 | Ollama | Free | Fast, local, and reliable. Used by default. |
| `text-embedding-3-small` | 1536 | OpenAI | $0.02/1M tokens | High quality, requires OpenAI API key. |
| `text-embedding-3-large` | 3072 | OpenAI | $0.13/1M tokens | Deepest semantic quality. |

**For fully offline embedding generation:**
Ensure Ollama is running and run:
```bash
ollama pull nomic-embed-text
```
Configure `EMBED_MODEL=nomic-embed-text` in `backend/.env`.

---

### 2.7 Data Sources

#### PubChem — Active (Phase 1+)
- **URL**: https://pubchem.ncbi.nlm.nih.gov
- **Auth**: None required. Rate limit: 5 requests/second.
- **Used for**: SMILES -> CID resolution, structure images, IUPAC name, molecular formula/weight, InChI, pharmacology text summaries.
- **Key API endpoints:**
  ```
  GET /compound/smiles/{smiles}/property/{fields}/JSON  -> compound properties
  GET /compound/CID/{cid}/PNG                           -> structure image
  GET /compound/CID/{cid}/description/JSON              -> pharmacology text
  ```

#### DailyMed / FDA — Phase 2
- **URL**: https://dailymed.nlm.nih.gov
- **Auth**: None required.
- **Used for**: Indications, contraindications, adverse effects, drug interactions, clinical pharmacology (ADME). Legally authoritative descriptions — primary source for all clinical fields.
- **Key API endpoints:**
  ```
  GET /services/v2/spls.json?drug_name={name}   -> search labels by drug name
  GET /services/v2/spls/{set_id}.json            -> full label with named sections
  ```

#### PubMed — Phase 2
- **URL**: https://pubmed.ncbi.nlm.nih.gov
- **Auth**: Optional NCBI API key raises rate limit from 3 to 10 req/s.
- **Used for**: Mechanistic detail for MoA, pharmacokinetic studies for ADME, research-level drug interaction data — enriches what FDA labels provide.
- **Key API endpoints (NCBI E-utilities):**
  ```
  GET /esearch.fcgi?db=pubmed&term={query}&retmax=N   -> search, returns PMIDs
  GET /efetch.fcgi?db=pubmed&id={pmids}&retmode=xml   -> fetch abstracts as XML
  ```

---

### 2.8 Schema Enforcement: Pydantic

**What it is**: Python data validation library. Defines the `DrugInfo` model every LLM response must conform to.

**Why schema enforcement matters:**
Without it, the LLM might return responses with missing keys or fabricated data. Pydantic validates the structure of the Gemini output before it is returned:
```python
# If LLM returns malformed JSON -> Pydantic raises ValidationError -> API triggers safe fallback
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
> "If data is not present in the provided context, set `missing: true` and `content: null`. Do NOT approximate, infer, or fabricate."

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
   b. build_retrieval_query(structure_data)
      -> Generates retrieval query from synonyms and IUPAC name
   c. retriever.retrieve(query, n_results=8, pubchem_cid=cid)
      -> Cosine similarity search filtered strictly for the matching drug CID
   d. Build context: Format chunk strings and construct source map mapping source ids
   e. system_prompt + context chunks + SMILES prompt construction
   f. llm.generate_structured_output(prompt)
      -> raw JSON string from Google Gemini API (using HTTP POST)
   g. resolve_field_citations(raw_dict, source_map)
      -> Map source_ids inside fields to real metadata citations (source name, URL)
   h. Pydantic validation -> DrugInfo(**parsed) -> Return validated schema
6. FastAPI returns { success: true, data: DrugInfo }
7. Next.js route returns JSON to browser
8. Frontend: appends assistant message with drugInfo
9. ChatInterface renders DrugInfoCard with all tabs populated
```

### Three-Layer Anti-Hallucination Stack

| Layer | Mechanism |
|---|---|
| **Retrieval** | LLM only sees retrieved chunks restricted by `pubchem_cid`, not its general training knowledge |
| **System prompt** | Explicit instruction: "answer ONLY from context; use missing:true if absent" |
| **Schema validation** | Pydantic rejects any response not conforming to DrugInfo shape, falling back to a structured "missing" response |

---

## 4. Phase 2 — Knowledge Base Construction

**Goal**: Ingest pharmaceutical text from DailyMed, PubMed, and PubChem into ChromaDB using local Ollama embeddings so Phase 3 retrieval has real data.

---

### Step 1 — Install Dependencies

Install the core dependencies inside your virtual environment:

```bash
cd backend
pip install chromadb httpx ollama pydantic fastapi uvicorn python-dotenv
```

Ensure Ollama is running locally and has the embedding model downloaded:
```bash
ollama pull nomic-embed-text
```

---

### Step 2 — Implement Ingestion Scripts

Ingestion helper functions fetch labels and abstracts:
- `backend/ingest/dailymed.py` parses DailyMed label sections (indications, adverse effects, ADME).
- `backend/ingest/pubmed.py` calls NCBI E-utilities to retrieve abstracts.
- `backend/ingest/pubchem.py` retrieves canonical structure information.

These are orchestrated via `backend/ingest/run_ingest.py`.

---

### Step 3 — Run the Ingestion Script

Run the ingestion script from the `backend` directory to construct the local vector database for benchmark drugs:

```bash
cd backend
python -m ingest.run_ingest
```

Upon success, you will see a console summary table listing the number of text chunks stored in ChromaDB per drug and field.

---

### Step 4 — Implement `rag/retriever.py`

Our retriever uses local Ollama to embed queries and performs a two-stage lookup (metadata filter by `pubchem_cid`, then vector search):

```python
import os
import chromadb
import ollama

CHROMA_PATH = os.getenv("CHROMA_PATH", "../data/chroma")
COLLECTION_NAME = "pharma_docs"
EMBED_MODEL = os.getenv("EMBED_MODEL", "nomic-embed-text")

def _embed(text: str) -> list[float]:
    resp = ollama.embed(model=EMBED_MODEL, input=text[:8000])
    return resp.embeddings[0]

class Retriever:
    def __init__(self):
        self.client = chromadb.PersistentClient(path=CHROMA_PATH)
        self.collection = self.client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
        self._ready = self.collection.count() > 0

    def is_ready(self) -> bool:
        return self._ready

    async def retrieve(self, query: str, n_results: int = 8, pubchem_cid: str | None = None) -> list[dict]:
        if not self._ready:
            return []

        query_vec = _embed(query)
        kwargs = {
            "query_embeddings": [query_vec],
            "n_results": n_results,
            "include": ["documents", "metadatas", "distances"],
        }
        if pubchem_cid:
            kwargs["where"] = {"pubchem_cid": pubchem_cid}

        results = self.collection.query(**kwargs)
        return [
            {
                "text": doc,
                "source": meta.get("source", ""),
                "url": meta.get("url", ""),
                "field": meta.get("field", ""),
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

**Goal**: Wire retrieval + Google Gemini + schema validation into a live API response.

---

### Step 1 — Configure environment variables

Create or open `backend/.env` and set:

```env
LLM_PROVIDER=gemini
GEMINI_API_KEY=your_google_gemini_api_key_here
GEMINI_MODEL=gemini-3.5-flash-lite

# Embeddings & ChromaDB configurations
EMBED_MODEL=nomic-embed-text
CHROMA_PATH=../data/chroma
```

---

### Step 2 — Implement `rag/llm.py` — Gemini Call

We call the Google Gemini API directly over HTTP POST, enabling the `responseMimeType: "application/json"` generation parameter:

```python
async def _call_gemini(
    system_prompt: str,
    user_message: str,
    schema: type[BaseModel],
) -> dict:
    """
    Call Google Gemini API with JSON mode.
    Requires: httpx and GEMINI_API_KEY env var.
    """
    import httpx
    import json

    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY environment variable is not set.")

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"

    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {"text": user_message}
                ]
            }
        ],
        "systemInstruction": {
            "parts": [
                {"text": system_prompt}
            ]
        },
        "generationConfig": {
            "responseMimeType": "application/json",
            "temperature": 0.1,
        }
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(url, json=payload)
        resp.raise_for_status()
        data = resp.json()

    try:
        raw = data["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError) as exc:
        raise ValueError(f"Gemini API returned unexpected response format: {data}") from exc

    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Gemini returned invalid JSON: {exc}\nRaw output (first 500 chars):\n{raw[:500]}"
        ) from exc
```

---

### Step 3 — Swap the Frontend Mock for a Real Backend Proxy

Update `frontend/app/api/query/route.ts` to proxy requests directly to the FastAPI server:

```typescript
import { NextRequest, NextResponse } from "next/server";

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

### Step 4 — Run the App

1. **Start the FastAPI backend**:
   ```bash
   cd backend
   uvicorn main:app --reload --port 8000
   ```
2. **Start the Next.js frontend**:
   ```bash
   cd frontend
   npm run dev
   ```
3. Open `http://localhost:3000` in the browser, enter a valid SMILES query (e.g. `CC(=O)Oc1ccccc1C(=O)O` for Aspirin), and inspect the verified structured outputs.

---

### Phase 3 Debugging Guide

| Symptom | Cause | Fix |
|---|---|---|
| `Gemini API key is not set` | Missing env variable in FastAPI | Check that `GEMINI_API_KEY` is set inside `backend/.env` and FastAPI was restarted. |
| `HTTP 403 / 400` from Gemini | Invalid API key or model name | Check the API key correctness and verify if your region supports the model configured in `GEMINI_MODEL`. |
| LLM returns invalid JSON | Temp config/prompt issue | Ensure `temperature` is low (0.1) and JSON mode is enforced in the payload. |
| ChromaDB returns 0 results | Ingestion not run, or query mismatch | Run `run_ingest.py` before querying; check that path matches. |
| All fields `missing: true` | Retrieval fetched empty results | Ensure ChromaDB contains data for the drug and query synonyms are correct. |

---

## 6. Environment Variables Reference

All variables go in `backend/.env` (copy from `backend/.env.example`).

| Variable | Default | Required | Description |
|---|---|---|---|
| `LLM_PROVIDER` | `gemini` | Yes | Model provider: `gemini` / `ollama` / `openai` / `anthropic` |
| `GEMINI_API_KEY` | — | If gemini | API Key from Google AI Studio |
| `GEMINI_MODEL` | `gemini-3.5-flash-lite` | If gemini | Gemini model name (e.g., `gemini-3.5-flash-lite` / `gemini-1.5-flash` / `gemini-1.5-pro`) |
| `EMBED_MODEL` | `nomic-embed-text` | Yes | Local text embedding model name |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | If ollama | Ollama server URL (if using ollama provider for LLM) |
| `OLLAMA_MODEL` | `qwen2.5:7b` | If ollama | Model name for local LLM (if using ollama provider for LLM) |
| `OPENAI_API_KEY` | — | If openai | sk-... |
| `OPENAI_MODEL` | `gpt-4o` | If openai | OpenAI model name |
| `ANTHROPIC_API_KEY` | — | If anthropic | sk-ant-... |
| `ANTHROPIC_MODEL` | `claude-3-5-sonnet-20241022` | If anthropic | Anthropic model name |
| `NCBI_API_KEY` | — | No | Optional key raising PubMed request limits |
| `CHROMA_PATH` | `../data/chroma` | Phase 2+ | Path to ChromaDB vector DB persistence directory |

---

## 7. File-by-File Reference

### Frontend

| File | Role | Next edit in Phase |
|---|---|---|
| `app/page.tsx` | Layout + chat state management | 2 (add loading skeleton) |
| `app/globals.css` | Design tokens + global styles | Any (visual changes) |
| `app/layout.tsx` | HTML root, SEO metadata | Any |
| `app/api/query/route.ts` | Next.js API router proxy | 3 |
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
| `rag/pipeline.py` | Full RAG pipeline orchestration | 3 |
| `rag/retriever.py` | Two-stage ChromaDB vector search | 2 (implement), 3 (tune n_results) |
| `rag/llm.py` | LLM provider client (implements Gemini/Ollama/OpenAI/Anthropic) | 3 |
| `ingest/pubchem.py` | PubChem REST API ingestion | 2 |
| `ingest/dailymed.py` | DailyMed FDA label scraping | 2 |
| `ingest/pubmed.py` | PubMed abstract retrieval | 2 |
| `ingest/run_ingest.py` | Main ingestion orchestration script | Create in Phase 2 |
| `prompts/drug_info.txt` | LLM system prompt template | 3 (tune for accuracy per field) |
| `.env.example` | Environment variable template | As new variables are added |

### Docs

| File | Primary audience |
|---|---|
| `docs/schema.md` | **Domain expert** — expected content + missing-data rules per field |
| `docs/data_sources.md` | **Both** — API references + ingestion strategy |
| `docs/DEVELOPMENT.md` | **Developer** — this document |
| `README.md` | **Anyone** — quick-start |
