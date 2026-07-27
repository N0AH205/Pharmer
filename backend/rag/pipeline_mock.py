"""
Mock pipeline data — Phase 1 fallback.

Used ONLY when the ChromaDB collection is empty (development before ingestion).
This keeps the frontend testable at all times.
"""

from rag.schema import (
    DrugInfo, DrugName, FieldValue, ADMEFields, ChemicalStructure, Citation
)

MOCK_ASPIRIN = DrugInfo(
    query_smiles="CC(=O)Oc1ccccc1C(=O)O",
    drug_name=DrugName(
        generic="Acetylsalicylic acid",
        brand_names=["Aspirin", "Bayer Aspirin", "Ecotrin", "Bufferin"],
        sources=[
            Citation(source="PubChem CID 2244", url="https://pubchem.ncbi.nlm.nih.gov/compound/2244"),
        ],
    ),
    chemical_structure=ChemicalStructure(
        smiles="CC(=O)Oc1ccccc1C(=O)O",
        inchi="InChI=1S/C9H8O4/c1-6(10)13-8-5-3-2-4-7(8)9(11)12/h2-5H,1H3,(H,11,12)",
        iupac_name="2-acetoxybenzoic acid",
        molecular_formula="C9H8O4",
        molecular_weight=180.16,
        pubchem_cid=2244,
        image_url="https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/CID/2244/PNG",
        sources=[Citation(source="PubChem CID 2244", url="https://pubchem.ncbi.nlm.nih.gov/compound/2244")],
    ),
    mechanism_of_action=FieldValue(
        content=(
            "Acetylsalicylic acid irreversibly inhibits COX-1 and COX-2 through acetylation "
            "of a serine residue (Ser530 on COX-1, Ser516 on COX-2), blocking conversion of "
            "arachidonic acid to prostaglandin H2 and reducing downstream prostaglandin, "
            "prostacyclin, and thromboxane A2 synthesis."
        ),
        sources=[Citation(source="PubChem CID 2244 — Pharmacology", url="https://pubchem.ncbi.nlm.nih.gov/compound/2244")],
    ),
    adme=ADMEFields(
        absorption=FieldValue(
            content="Rapidly absorbed from the GI tract; ~50–68% bioavailability; peak salicylate concentrations in 1–2 hours.",
            sources=[Citation(source="DailyMed SPL — Aspirin", url="https://dailymed.nlm.nih.gov")],
        ),
        distribution=FieldValue(
            content="Widely distributed; ~80–90% plasma protein binding (albumin); Vd ~0.17 L/kg.",
            sources=[Citation(source="DailyMed SPL — Aspirin", url="https://dailymed.nlm.nih.gov")],
        ),
        metabolism=FieldValue(
            content="Hydrolyzed to salicylate in GI mucosa, plasma, and liver; conjugated with glycine (salicyluric acid) and glucuronic acid.",
            sources=[Citation(source="DailyMed SPL — Aspirin", url="https://dailymed.nlm.nih.gov")],
        ),
        excretion=FieldValue(
            content="Renally excreted; t½ 2–3 h (low dose), 15–30 h (high dose); excretion pH-dependent.",
            sources=[Citation(source="DailyMed SPL — Aspirin", url="https://dailymed.nlm.nih.gov")],
        ),
    ),
    indications=FieldValue(
        content="Pain, fever, inflammation, antiplatelet (MI/stroke prevention), Kawasaki disease, pre-eclampsia prevention.",
        sources=[Citation(source="DailyMed SPL — Aspirin", url="https://dailymed.nlm.nih.gov")],
    ),
    contraindications=FieldValue(
        content="Hypersensitivity to aspirin/NSAIDs, children with viral illness (Reye's syndrome), active GI bleeding, bleeding disorders, 3rd trimester pregnancy.",
        sources=[Citation(source="DailyMed SPL — Aspirin", url="https://dailymed.nlm.nih.gov")],
    ),
    adverse_effects=FieldValue(
        content="GI irritation, GI haemorrhage, tinnitus (salicylism), hypersensitivity, Reye's syndrome (children), AERD.",
        sources=[Citation(source="DailyMed SPL — Aspirin", url="https://dailymed.nlm.nih.gov")],
    ),
    drug_interactions=FieldValue(
        content="Warfarin (bleeding risk), ibuprofen (antiplatelet antagonism), methotrexate (toxicity), SSRIs (bleeding), ACE inhibitors (reduced antihypertensive effect).",
        sources=[Citation(source="DailyMed SPL — Aspirin", url="https://dailymed.nlm.nih.gov")],
    ),
)
