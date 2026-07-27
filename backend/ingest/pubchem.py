"""
PubChem data fetcher.

Uses the PubChem PUG REST API (free, no auth required).
Active in Phase 1+; expanded in Phase 2 to return common names and synonyms
so that the retrieval query builder can construct better search strings.

Key endpoints:
  - /compound/smiles/{smiles}/property/{props}/JSON  → compound properties
  - /compound/CID/{cid}/PNG                          → structure image
  - /compound/CID/{cid}/description/JSON             → pharmacology text
  - /compound/CID/{cid}/synonyms/JSON                → common names / synonyms

Docs: https://pubchemdocs.ncbi.nlm.nih.gov/pug-rest
"""

from __future__ import annotations

import re
import urllib.parse

import httpx

BASE_URL = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"

PROPERTY_FIELDS = ",".join([
    "IUPACName",
    "MolecularFormula",
    "MolecularWeight",
    "CanonicalSMILES",
    "InChI",
    "InChIKey",
])

# Patterns that identify non-human-readable identifiers we want to skip
_CAS_RE = re.compile(r"^\d{2,7}-\d{2}-\d$")
_INCHI_RE = re.compile(r"^InChI=")
_NUMERIC_RE = re.compile(r"^\d+$")


def _is_readable_name(name: str) -> bool:
    """Return True if a synonym looks like a human-readable name (not a CAS, InChI, etc.)."""
    if _CAS_RE.match(name):
        return False
    if _INCHI_RE.match(name):
        return False
    if _NUMERIC_RE.match(name):
        return False
    if len(name) > 80:  # excessively long strings are usually database codes
        return False
    return True


async def get_compound_by_smiles(smiles: str) -> dict | None:
    """
    Resolve a SMILES string to PubChem compound properties.
    Returns a dict with CID, IUPACName, MolecularFormula, etc., or None if not found.
    """
    encoded = urllib.parse.quote(smiles, safe="")
    url = f"{BASE_URL}/compound/smiles/{encoded}/property/{PROPERTY_FIELDS}/JSON"

    async with httpx.AsyncClient(timeout=15) as client:
        try:
            resp = await client.get(url)
            if resp.status_code != 200:
                return None
            data = resp.json()
            props = data.get("PropertyTable", {}).get("Properties", [])
            return props[0] if props else None
        except Exception:
            return None


async def get_synonyms(cid: int, max_synonyms: int = 10) -> list[str]:
    """
    Fetch human-readable synonyms for a PubChem CID.

    Returns a filtered list of common names (e.g. ["aspirin",
    "acetylsalicylic acid", ...]), excluding CAS numbers, InChI strings,
    and other non-human-readable identifiers.
    """
    url = f"{BASE_URL}/compound/CID/{cid}/synonyms/JSON"
    async with httpx.AsyncClient(timeout=15) as client:
        try:
            resp = await client.get(url)
            if resp.status_code != 200:
                return []
            data = resp.json()
            all_synonyms: list[str] = (
                data.get("InformationList", {})
                    .get("Information", [{}])[0]
                    .get("Synonym", [])
            )
        except Exception:
            return []

    readable = [s for s in all_synonyms if _is_readable_name(s)]
    return readable[:max_synonyms]


async def get_structure_image_url(cid: int) -> str:
    """Return the PNG structure image URL for a PubChem CID."""
    return f"{BASE_URL}/compound/CID/{cid}/PNG"


async def get_pharmacology_text(cid: int) -> str | None:
    """
    Fetch the pharmacology / description text for a compound.
    Used in Phase 2 for knowledge base ingestion.
    """
    url = f"{BASE_URL}/compound/CID/{cid}/description/JSON"
    async with httpx.AsyncClient(timeout=15) as client:
        try:
            resp = await client.get(url)
            if resp.status_code != 200:
                return None
            data = resp.json()
            descriptions = data.get("InformationList", {}).get("Information", [])
            texts = [
                info["Description"]
                for info in descriptions
                if "Description" in info and info.get("DescriptionSourceName") != "Wikipedia"
            ]
            return "\n\n".join(texts) if texts else None
        except Exception:
            return None


async def get_compound_by_name(name: str) -> dict | None:
    """
    Resolve a compound name to PubChem compound properties.
    Returns a dict with CID, IUPACName, MolecularFormula, etc., or None if not found.
    """
    encoded = urllib.parse.quote(name, safe="")
    url = f"{BASE_URL}/compound/name/{encoded}/property/{PROPERTY_FIELDS}/JSON"

    async with httpx.AsyncClient(timeout=15) as client:
        try:
            resp = await client.get(url)
            if resp.status_code != 200:
                return None
            data = resp.json()
            props = data.get("PropertyTable", {}).get("Properties", [])
            return props[0] if props else None
        except Exception:
            return None


async def enrich_structure(smiles: str) -> dict:
    """
    Main helper: given a SMILES, return a dict suitable for ChemicalStructure.

    Fetches synonyms so the query builder can use the common name (e.g. "Aspirin").
    If SMILES lookup resolves to an isotope/derivative entry (e.g. [14C]metformin),
    cross-checks against common_name via PubChem name resolution to obtain the
    parent compound CID (e.g. CID 4091).
    """
    props = await get_compound_by_smiles(smiles)
    if not props:
        return {
            "smiles": smiles,
            "pubchem_cid": None,
            "iupac_name": None,
            "common_name": None,
            "synonyms": [],
            "image_url": None,
            "sources": [],
        }

    cid = props.get("CID")
    iupac = props.get("IUPACName")

    # Fetch synonyms to get the common/trade name
    synonyms = await get_synonyms(cid) if cid else []

    # The common name is the first synonym that differs from the IUPAC name
    iupac_lower = (iupac or "").lower()
    common_name: str | None = next(
        (s for s in synonyms if s.lower() != iupac_lower),
        None,
    )

    # Check if name lookup for common_name gives a canonical parent compound CID
    if common_name:
        clean_name = re.sub(r"^\[.*?\]-?", "", common_name).strip()
        parent_props = await get_compound_by_name(clean_name)
        if parent_props and parent_props.get("CID"):
            parent_cid = parent_props["CID"]
            # If parent CID is different (e.g. 4091 vs 152743144), adopt the parent CID & props
            if parent_cid != cid:
                props = parent_props
                cid = parent_cid
                common_name = clean_name
                iupac = props.get("IUPACName") or iupac
                parent_syns = await get_synonyms(cid)
                if parent_syns:
                    synonyms = parent_syns

    return {
        "smiles": props.get("CanonicalSMILES") or props.get("ConnectivitySMILES") or smiles,
        "inchi": props.get("InChI"),
        "iupac_name": iupac,
        "common_name": common_name,
        "synonyms": synonyms,
        "molecular_formula": props.get("MolecularFormula"),
        "molecular_weight": float(props["MolecularWeight"]) if props.get("MolecularWeight") else None,
        "pubchem_cid": cid,
        "image_url": await get_structure_image_url(cid) if cid else None,
        "sources": [
            {
                "source": f"PubChem CID {cid}",
                "url": f"https://pubchem.ncbi.nlm.nih.gov/compound/{cid}",
            }
        ] if cid else [],
    }
