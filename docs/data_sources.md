# Data Sources

Reference for all data sources used in the Pharma RAG system.

---

## PubChem ✅ Active (Phase 1+)

- **URL**: https://pubchem.ncbi.nlm.nih.gov
- **API**: PUG REST — https://pubchemdocs.ncbi.nlm.nih.gov/pug-rest
- **Auth**: None required
- **Rate limit**: 5 requests/second
- **Scale**: 120M+ compounds
- **Used for**: Chemical structure, IUPAC name, molecular formula/weight, InChI, structure images, pharmacology text

### Key endpoints
```
GET /compound/smiles/{smiles}/property/{fields}/JSON   → compound properties
GET /compound/CID/{cid}/PNG                            → structure image
GET /compound/CID/{cid}/description/JSON               → pharmacology text
```

---

## DailyMed / FDA 🔜 Phase 2

- **URL**: https://dailymed.nlm.nih.gov
- **API**: DailyMed Web Services v2 — https://dailymed.nlm.nih.gov/dailymed/app-support-web-services.cfm
- **Auth**: None required
- **Scale**: 150k+ FDA-approved drug labels
- **Used for**: Indications, contraindications, adverse effects, drug interactions, ADME (clinical pharmacology section)

### Key endpoints
```
GET /services/v2/spls.json?drug_name={name}   → search labels
GET /services/v2/spls/{set_id}.json           → full label
```

---

## PubMed 🔜 Phase 2

- **URL**: https://pubmed.ncbi.nlm.nih.gov
- **API**: NCBI E-utilities — https://www.ncbi.nlm.nih.gov/books/NBK25497/
- **Auth**: Optional — NCBI_API_KEY raises rate limit from 3 to 10 req/s
- **Scale**: 38M+ citations
- **Used for**: MoA detail, pharmacokinetics, clinical evidence, drug interactions research

### Key endpoints
```
GET /esearch.fcgi?db=pubmed&term={query}&retmax=N   → search → PMIDs
GET /efetch.fcgi?db=pubmed&id={pmids}&retmode=xml   → fetch abstracts
```

---

## DrugBank ⏸ Requires License

- **URL**: https://www.drugbank.ca
- **Auth**: Academic/personal license is free; commercial use requires paid subscription
- **Scale**: 14k+ drugs with structured MoA, ADME, and interaction data
- **Used for**: Detailed MoA, complete ADME, structured drug interaction database

> **Status**: Stubbed. Will be integrated once license is confirmed.
> For academic/research use, apply at: https://www.drugbank.ca/legal/terms_of_use

---

## Ingestion Strategy (Phase 2)

1. For each drug in the benchmark set:
   - Fetch PubChem data → embed → store in ChromaDB
   - Fetch DailyMed label → parse sections → chunk → embed → store
   - Fetch top-20 PubMed abstracts → embed → store
2. Metadata stored with each chunk: source name, URL, drug name, field type
3. At query time, ChromaDB retrieves top-K chunks by cosine similarity to SMILES/drug query
