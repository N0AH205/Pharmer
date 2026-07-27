# Pharma RAG System

A Retrieval-Augmented Generation (RAG) chatbot for structured drug-information queries.
Accepts a SMILES string, retrieves data from pharmaceutical sources, and returns a
structured response (MoA, ADME, Chemical Structure, Indications, Contraindications,
Adverse Effects, Drug Interactions) — grounded in cited sources, never hallucinated.

## Project Structure

```
pharma-rag/
├── frontend/     # Next.js 14 app (TypeScript)
├── backend/      # Python FastAPI RAG server
├── data/         # Local ChromaDB vector store (gitignored)
├── docs/         # Schema definitions, data source notes
└── README.md
```

## Quick Start

### Frontend
```bash
cd frontend
npm install
npm run dev
# → http://localhost:3000
```

### Backend
```bash
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
cp .env.example .env          # Fill in your keys
uvicorn main:app --reload
# → http://localhost:8000
```

## LLM Provider

Set `LLM_PROVIDER` in `backend/.env`:

| Value | Description |
|---|---|
| `ollama` | Local Qwen/Llama via Ollama (default) |
| `openai` | OpenAI GPT-4o |
| `anthropic` | Anthropic Claude |

For Qwen locally: install [Ollama](https://ollama.com), then run:
```bash
ollama pull qwen2.5:72b
```

## Development Phases

- **Phase 1 (current)** — Scaffold: UI shell + stubbed backend + PubChem structure lookup
- **Phase 2** — Knowledge base: ingest DailyMed, PubMed, PubChem into ChromaDB
- **Phase 3** — RAG pipeline: query → retrieval → Qwen structured output
- **Phase 4** — Evaluation: benchmark set + gold-standard comparison
- **Phase 5** — Safety layer: citations, disclaimers, refusal behavior

## Data Sources

| Source | Type | Status |
|---|---|---|
| PubChem | Structure + basic properties | ✅ Active |
| DailyMed / FDA | Drug labels | 🔜 Phase 2 |
| PubMed | Research abstracts | 🔜 Phase 2 |
| DrugBank | MoA, ADME, interactions | ⏸ Requires license |

## Disclaimer

This tool is for **educational and reference purposes only**. It does not constitute
clinical advice. Always consult a licensed clinician or pharmacist for patient-specific
guidance.
