"""
Mock pipeline data — Phase 1 fallback.

Used ONLY when the ChromaDB collection is empty (development before ingestion).
This keeps the frontend testable at all times.
"""

from rag.schema import (
    DrugInfo, DrugName, FieldValue, ADMEFields, ChemicalStructure, Citation,
    PharmacodynamicsFields, ToxicologyFields, TherapeuticProfile, HistoryFields,
)

MOCK_ASPIRIN = DrugInfo(
    query_smiles="CC(=O)Oc1ccccc1C(=O)O",
    drug_name=DrugName(
        generic="Acetylsalicylic acid",
        brand_names=["Aspirin", "Bayer Aspirin", "Ecotrin", "Bufferin"],
        lab_codes=["BAY-09867", "2-Acetoxybenzoic acid", "o-Acetoxybenzoic acid"],
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
    therapeutic_classes=FieldValue(
        content=(
            "Broad clinical category: Non-Steroidal Anti-Inflammatory Drug (NSAID), Analgesic, "
            "Antipyretic, and Antiplatelet agent.\n"
            "Pharmacological classification: Cyclooxygenase (COX) inhibitor — non-selective, "
            "irreversible inhibitor of both COX-1 and COX-2 isoenzymes. Also classified under "
            "salicylates (salicylic acid derivatives)."
        ),
        sources=[Citation(source="PubChem CID 2244 — Pharmacology", url="https://pubchem.ncbi.nlm.nih.gov/compound/2244")],
    ),
    pharmacodynamics=PharmacodynamicsFields(
        mechanism_of_action=FieldValue(
            content=(
                "Step 1 — Absorption and hydrolysis: Aspirin is absorbed intact and partially "
                "hydrolyzed to salicylate in the GI mucosa and liver.\n"
                "Step 2 — Irreversible acetylation: The acetyl group of aspirin covalently "
                "acetylates the hydroxyl group of Serine-530 (Ser530) on COX-1 and Serine-516 "
                "(Ser516) on COX-2, permanently blocking the enzyme's active site.\n"
                "Step 3 — Arachidonic acid pathway blockade: Acetylated COX enzymes can no longer "
                "convert arachidonic acid to Prostaglandin H2 (PGH2), the common precursor for "
                "all prostanoids.\n"
                "Step 4 — Downstream prostanoid suppression: Reduced PGH2 leads to decreased "
                "synthesis of prostaglandins (PGE2, PGI2) responsible for pain, fever, and "
                "inflammation, and thromboxane A2 (TXA2), a potent platelet aggregator and "
                "vasoconstrictor.\n"
                "Step 5 — Irreversible platelet effect: Platelets lack nuclei and cannot "
                "re-synthesize COX-1, so antiplatelet effects persist for the platelet's "
                "entire lifespan (~7–10 days)."
            ),
            sources=[Citation(source="PubChem CID 2244 — Pharmacology", url="https://pubchem.ncbi.nlm.nih.gov/compound/2244")],
        ),
        physiologic_effect=FieldValue(
            content=(
                "Anti-inflammatory effect: Reduced prostaglandin synthesis decreases vasodilation, "
                "vascular permeability, and sensitization of peripheral pain receptors.\n"
                "Analgesic effect: Peripheral and central reduction of prostaglandin-mediated "
                "pain sensitization (hyperalgesia).\n"
                "Antipyretic effect: Inhibition of PGE2 synthesis in the hypothalamus, restoring "
                "the thermoregulatory set-point to normal.\n"
                "Antiplatelet effect: Permanent inhibition of platelet TXA2 synthesis prevents "
                "platelet aggregation and reduces thrombotic risk.\n"
                "High-dose uricosuric effect: At doses >3 g/day, aspirin inhibits tubular "
                "reabsorption of uric acid, promoting its excretion."
            ),
            sources=[Citation(source="DailyMed SPL — Aspirin", url="https://dailymed.nlm.nih.gov")],
        ),
        binding_affinity=FieldValue(
            content=(
                "COX-1: Covalent irreversible binding (pseudo-IC50 ~1–10 µM for platelet "
                "TXA2 inhibition in vivo).\n"
                "COX-2: Covalent irreversible binding (IC50 ~50–100 µM for anti-inflammatory "
                "effect).\n"
                "Salicylate (active metabolite): Non-covalent, reversible COX inhibition with "
                "IC50 in the high micromolar range (~1–5 mM).\n"
                "Note: Exact Kd values for aspirin are not reported in standard references "
                "due to its covalent, time-dependent inhibition mechanism."
            ),
            sources=[Citation(source="PubChem CID 2244 — Pharmacology", url="https://pubchem.ncbi.nlm.nih.gov/compound/2244")],
        ),
        selectivity=FieldValue(
            content=(
                "Aspirin is a non-selective COX inhibitor with modest preference for COX-1 "
                "over COX-2 (COX-1 IC50 ~1–10 µM vs. COX-2 IC50 ~50–100 µM at steady state).\n"
                "At low antiplatelet doses (81 mg/day), selectivity for platelet COX-1 is "
                "functionally achieved due to presystemic exposure of portal platelets.\n"
                "At higher doses, COX-2 is also inhibited, providing anti-inflammatory but "
                "also GI-protective prostacyclin (PGI2) suppression, increasing GI risk.\n"
                "Off-target: Aspirin has minimal affinity for other enzyme systems at "
                "therapeutic concentrations."
            ),
            sources=[Citation(source="DailyMed SPL — Aspirin", url="https://dailymed.nlm.nih.gov")],
        ),
        potency=FieldValue(
            content=(
                "Antiplatelet (TXA2 inhibition): ED50 ~40–80 mg/day orally in humans.\n"
                "Antipyretic/Analgesic: Effective dose 325–650 mg every 4–6 hours; EC50 for "
                "antipyresis not precisely defined in humans due to complex PK/PD relationship.\n"
                "Anti-inflammatory: Typically requires 3–6 g/day; EC50 in the high salicylate "
                "plasma concentration range (~150–300 µg/mL).\n"
                "In vitro COX-1 acetylation IC50: ~1.7 µM (aspirin) in cell-free assays."
            ),
            sources=[Citation(source="DailyMed SPL — Aspirin", url="https://dailymed.nlm.nih.gov")],
        ),
        efficacy=FieldValue(
            content=(
                "Antiplatelet (Emax): Near-complete (>95%) inhibition of platelet TXA2 "
                "synthesis at antiplatelet doses (75–100 mg/day) — considered a full agonist "
                "for this endpoint.\n"
                "Anti-inflammatory (Emax): Incomplete — aspirin is a partial anti-inflammatory "
                "agent compared to selective COX-2 inhibitors (celecoxib) due to preferential "
                "COX-1 inhibition and dose-limiting GI toxicity before full COX-2 saturation.\n"
                "Antipyresis (Emax): Complete normalization of fever when prostanoid-driven, "
                "though underlying infection is unaffected."
            ),
            sources=[Citation(source="PubChem CID 2244 — Pharmacology", url="https://pubchem.ncbi.nlm.nih.gov/compound/2244")],
        ),
    ),
    adme=ADMEFields(
        absorption=FieldValue(
            content=(
                "Oral bioavailability (F): ~50–68% for aspirin (parent compound); "
                "salicylate bioavailability ~100%.\n"
                "Tmax: Peak aspirin plasma concentration in ~0.3–2 hours; peak salicylate "
                "in 1–2 hours post-dose.\n"
                "Absorption site: Primarily proximal small intestine (passive diffusion at "
                "low pH); also absorbed in the stomach.\n"
                "Food effect: Food slows absorption without significantly reducing extent.\n"
                "Enteric-coated formulations delay Tmax by 3–6 hours."
            ),
            sources=[Citation(source="DailyMed SPL — Aspirin", url="https://dailymed.nlm.nih.gov")],
        ),
        distribution=FieldValue(
            content=(
                "Volume of distribution (Vd): ~0.17 L/kg for salicylate.\n"
                "Plasma protein binding: ~80–90% (primarily albumin); saturable at high "
                "concentrations, leading to non-linear PK.\n"
                "Tissue distribution: Widely distributed to most body tissues; crosses the "
                "placental barrier and is present in breast milk.\n"
                "Blood-brain barrier (BBB): Limited penetration under normal conditions; "
                "CNS effects at toxic salicylate levels suggest some BBB crossing.\n"
                "Synovial fluid: Achieves therapeutic concentrations relevant to "
                "anti-inflammatory use."
            ),
            sources=[Citation(source="DailyMed SPL — Aspirin", url="https://dailymed.nlm.nih.gov")],
        ),
        metabolism=FieldValue(
            content=(
                "Primary pathway: Rapid hydrolysis of aspirin to salicylate (acetic acid + "
                "salicylic acid) by esterases in the GI mucosa, plasma, and liver — occurs "
                "within minutes of absorption.\n"
                "Salicylate conjugation (hepatic, saturable):\n"
                "  • Glycine conjugation → salicyluric acid (major pathway, ~75%)\n"
                "  • Glucuronidation → salicyl acyl glucuronide and salicyl phenolic glucuronide\n"
                "  • Oxidation → gentisic acid (minor, ~1%)\n"
                "Enzymes: UGT (glucuronosyltransferases) and SULT (sulfotransferases); "
                "CYP450 enzymes play a minimal role.\n"
                "Saturable Michaelis-Menten kinetics at higher doses cause non-linear, "
                "dose-dependent t½ prolongation."
            ),
            sources=[Citation(source="DailyMed SPL — Aspirin", url="https://dailymed.nlm.nih.gov")],
        ),
        excretion=FieldValue(
            content=(
                "Route: Primarily renal (urine) as salicylate and its conjugated metabolites.\n"
                "Clearance (CL): ~1 mL/min/kg at low doses; decreases significantly at "
                "high doses due to metabolic saturation.\n"
                "Elimination half-life (t½):\n"
                "  • Aspirin (parent): ~15–20 minutes\n"
                "  • Salicylate (low dose, 0.5–1 g): ~2–3 hours\n"
                "  • Salicylate (anti-inflammatory dose, >3 g): ~12–15 hours\n"
                "  • Salicylate (toxic dose): up to 30 hours\n"
                "pH dependence: Urinary alkalinization significantly increases salicylate "
                "renal clearance (ion trapping); used therapeutically in salicylate overdose."
            ),
            sources=[Citation(source="DailyMed SPL — Aspirin", url="https://dailymed.nlm.nih.gov")],
        ),
    ),
    toxicology=ToxicologyFields(
        ld50=FieldValue(
            content=(
                "Mouse (oral): LD50 ~250 mg/kg\n"
                "Rat (oral): LD50 ~200 mg/kg\n"
                "Dog (oral): LD50 ~400 mg/kg\n"
                "Cat (oral): LD50 ~40 mg/kg (cats are notably sensitive due to limited "
                "glucuronidation capacity)\n"
                "Note: Human extrapolation from animal LD50 is not directly applicable; "
                "toxic doses in humans are much lower on a mg/kg basis."
            ),
            sources=[Citation(source="PubChem CID 2244 — Toxicology", url="https://pubchem.ncbi.nlm.nih.gov/compound/2244")],
        ),
        toxic_doses=FieldValue(
            content=(
                "Salicylism (mild toxicity): Serum salicylate >200–300 µg/mL; tinnitus, "
                "hearing loss, nausea, vomiting.\n"
                "Moderate toxicity: Salicylate 300–500 µg/mL; hyperpnea, fever, metabolic "
                "acidosis, altered mental status.\n"
                "Severe/life-threatening toxicity: Salicylate >500 µg/mL; CNS toxicity, "
                "pulmonary edema, cardiovascular collapse.\n"
                "Estimated lethal dose in adults: ~30–40 g (acute ingestion); as little as "
                "150–200 mg/kg may be toxic in children."
            ),
            sources=[Citation(source="DailyMed SPL — Aspirin", url="https://dailymed.nlm.nih.gov")],
        ),
        organ_toxicity=FieldValue(
            content=(
                "Gastrointestinal: COX-1 inhibition reduces gastroprotective prostaglandins "
                "(PGE2, PGI2), leading to mucosal erosion, peptic ulcers, and GI haemorrhage "
                "(risk even at low antiplatelet doses).\n"
                "Hepatic: High-dose or chronic use can cause transient elevation of liver "
                "enzymes; rare hepatotoxicity (Reye's syndrome in children with viral illness).\n"
                "Renal: Inhibition of renal prostaglandins reduces GFR and may precipitate "
                "acute kidney injury in susceptible patients (elderly, heart failure, CKD).\n"
                "Hematologic: Irreversible inhibition of platelet COX-1 prolongs bleeding time; "
                "risk of haemorrhage.\n"
                "CNS: At toxic levels, salicylate uncouples oxidative phosphorylation and "
                "causes cerebral edema, confusion, seizures."
            ),
            sources=[Citation(source="DailyMed SPL — Aspirin", url="https://dailymed.nlm.nih.gov")],
        ),
        overdose_management=FieldValue(
            content=(
                "Immediate: Gastric decontamination (activated charcoal if within 1–2 hours "
                "and patient alert); do NOT induce emesis.\n"
                "Urinary alkalinization: IV sodium bicarbonate (target urine pH 7.5–8.0) "
                "greatly enhances renal salicylate excretion via ion trapping — key therapeutic "
                "intervention.\n"
                "IV fluids: Aggressive hydration to correct dehydration and support renal "
                "clearance.\n"
                "Glucose: Supplemental dextrose even if euglycemic, as CNS glucose may be "
                "depleted despite normal serum glucose.\n"
                "Hemodialysis: Indicated for severe toxicity (salicylate >800 µg/mL, acute "
                "kidney injury, refractory acidosis, pulmonary edema, or altered mental status).\n"
                "No specific antidote exists; management is supportive."
            ),
            sources=[Citation(source="DailyMed SPL — Aspirin", url="https://dailymed.nlm.nih.gov")],
        ),
    ),
    therapeutic_profile=TherapeuticProfile(
        indications=FieldValue(
            content=(
                "Approved uses:\n"
                "  • Mild to moderate pain (headache, musculoskeletal, dental, menstrual)\n"
                "  • Fever reduction (antipyresis)\n"
                "  • Inflammatory conditions: rheumatoid arthritis, osteoarthritis, "
                "pericarditis, rheumatic fever\n"
                "  • Cardiovascular prevention: secondary prevention of MI, stroke, "
                "unstable angina; primary prevention in selected high-risk individuals\n"
                "  • Kawasaki disease (with IVIG — pediatric use under specialist supervision)\n"
                "Key off-label uses:\n"
                "  • Pre-eclampsia prevention in high-risk pregnancies (low-dose, 1st trimester)\n"
                "  • Colorectal cancer chemoprevention (ongoing research)"
            ),
            sources=[Citation(source="DailyMed SPL — Aspirin", url="https://dailymed.nlm.nih.gov")],
        ),
        contraindications=FieldValue(
            content=(
                "Absolute contraindications:\n"
                "  • Known hypersensitivity to aspirin or any NSAID (risk of anaphylaxis)\n"
                "  • Aspirin-Exacerbated Respiratory Disease (AERD / Samter's triad)\n"
                "  • Active peptic ulcer or GI bleeding\n"
                "  • Haemorrhagic disorders (haemophilia, thrombocytopenia)\n"
                "  • Children and teenagers with viral illness (risk of Reye's syndrome)\n"
                "  • Third trimester of pregnancy (premature closure of ductus arteriosus, "
                "maternal haemorrhage)\n"
                "Relative contraindications:\n"
                "  • Severe hepatic impairment\n"
                "  • Moderate-to-severe renal impairment (GFR <30 mL/min)\n"
                "  • Concurrent anticoagulant or thrombolytic therapy\n"
                "  • Gout at low doses (can elevate uric acid and precipitate attacks)"
            ),
            sources=[Citation(source="DailyMed SPL — Aspirin", url="https://dailymed.nlm.nih.gov")],
        ),
        adverse_effects=FieldValue(
            content=(
                "Common (>1/100):\n"
                "  • GI irritation, nausea, dyspepsia, epigastric pain\n"
                "  • Prolonged bleeding time\n"
                "  • Tinnitus and hearing impairment (dose-related, early sign of toxicity)\n"
                "Less common (1/100–1/1000):\n"
                "  • Peptic ulcer, GI haemorrhage (can occur without preceding GI symptoms)\n"
                "  • Hypersensitivity reactions: urticaria, angioedema, bronchospasm\n"
                "  • Elevated liver enzymes\n"
                "Rare but serious (<1/1000):\n"
                "  • Intracranial haemorrhage (especially in elderly or with anticoagulants)\n"
                "  • Severe bronchoconstriction in AERD patients\n"
                "  • Reye's syndrome (children with viral illness)\n"
                "  • Aplastic anemia (extremely rare)"
            ),
            sources=[Citation(source="DailyMed SPL — Aspirin", url="https://dailymed.nlm.nih.gov")],
        ),
        drug_interactions=FieldValue(
            content=(
                "Warfarin / anticoagulants: Additive bleeding risk (both antiplatelet effect "
                "and protein binding displacement); management — avoid combination or use with "
                "strict monitoring; use lowest effective aspirin dose.\n"
                "Ibuprofen / other NSAIDs: Ibuprofen competitively antagonizes aspirin's "
                "irreversible COX-1 acetylation (take aspirin ≥2 hours before ibuprofen).\n"
                "Methotrexate: Aspirin reduces methotrexate renal clearance → methotrexate "
                "toxicity; avoid combination or reduce methotrexate dose and monitor.\n"
                "SSRIs / SNRIs: Additive GI bleeding risk (serotonin-mediated platelet "
                "activation inhibition synergy); monitor for signs of bleeding.\n"
                "ACE inhibitors: Aspirin may blunt antihypertensive effect by reducing "
                "prostaglandin-mediated vasodilation; monitor BP.\n"
                "Antidiabetic agents: May potentiate hypoglycemic effect of insulin and "
                "sulfonylureas at high aspirin doses.\n"
                "Probenecid / uricosurics: Low-dose aspirin antagonizes uricosuric effect — "
                "avoid in gout patients using uricosurics."
            ),
            sources=[Citation(source="DailyMed SPL — Aspirin", url="https://dailymed.nlm.nih.gov")],
        ),
    ),
    history=HistoryFields(
        background=FieldValue(
            content=(
                "By the 19th century, fever, pain, and inflammatory diseases such as "
                "rheumatism represented major unmet medical needs, with few effective and "
                "safe treatments available. Salicin, extracted from willow bark (Salix alba), "
                "had been used empirically since ancient times across multiple civilizations "
                "(Egyptians, Greeks, Native Americans) for pain and fever. The scientific "
                "foundation was established by Reverend Edward Stone, who in 1763 formally "
                "documented the therapeutic efficacy of willow bark extract in a letter to "
                "the Royal Society of London. The unmet need was a compound that retained "
                "salicylate's efficacy while minimizing its severe gastric irritation."
            ),
            sources=[Citation(source="PubChem CID 2244", url="https://pubchem.ncbi.nlm.nih.gov/compound/2244")],
        ),
        discovery=FieldValue(
            content=(
                "1828: Johann Andreas Buchner at the University of Munich isolated salicin "
                "from willow bark in purified form.\n"
                "1838: Raffaele Piria (Italian chemist) converted salicin to salicylic acid — "
                "the direct precursor.\n"
                "1853: Charles Frédéric Gerhardt (French chemist) first synthesized acetyl "
                "salicylic acid (aspirin) by reacting salicylic acid with acetyl chloride, but "
                "the product was impure and he did not recognize its significance.\n"
                "1897: Felix Hoffmann, a chemist at Bayer AG, re-synthesized and stabilized "
                "a pure, stable form of acetylsalicylic acid, motivated by the desire to "
                "reduce his father's rheumatism-related suffering from the GI side effects "
                "of sodium salicylate."
            ),
            sources=[Citation(source="PubChem CID 2244", url="https://pubchem.ncbi.nlm.nih.gov/compound/2244")],
        ),
        development=FieldValue(
            content=(
                "1897–1899: Bayer's pharmacologist Heinrich Dreser conducted early animal "
                "and human testing, confirming superior GI tolerability compared to "
                "salicylic acid.\n"
                "1899: Bayer trademarked the name 'Aspirin' — 'A' from acetyl, 'spir' from "
                "Spiraea ulmaria (meadowsweet, an acetylsalicylic acid source) — and "
                "launched it commercially as a powder.\n"
                "1915: Aspirin became available in tablet form without a prescription.\n"
                "Patent history: The original Bayer patent expired in Germany in 1917 as "
                "war reparations; 'Aspirin' remains a protected trademark in some countries "
                "(e.g., Germany, Canada) but is a generic name in the US, UK, and Australia.\n"
                "1970s: Mechanism of action elucidated by John Robert Vane (Nobel Prize 1982) "
                "demonstrating prostaglandin synthesis inhibition."
            ),
            sources=[Citation(source="PubChem CID 2244", url="https://pubchem.ncbi.nlm.nih.gov/compound/2244")],
        ),
        clinical_trials=FieldValue(
            content=(
                "1948–1960s: Early clinical studies established aspirin's role in pain and "
                "fever; formal RCT methodology was in its infancy.\n"
                "1974: First major RCT (Elwood et al., BMJ) showed aspirin reduced "
                "re-infarction mortality, though not statistically significant.\n"
                "1980: ISIS-2 trial demonstrated that aspirin (160 mg) combined with "
                "streptokinase significantly reduced mortality after acute MI.\n"
                "1988: Physicians' Health Study (US, n=22,071): Low-dose aspirin (325 mg "
                "every other day) reduced first MI risk by 44% in healthy male physicians.\n"
                "1994: Antithrombotic Trialists' Collaboration meta-analysis established "
                "aspirin's benefit in secondary cardiovascular prevention.\n"
                "2018: ARRIVE, ASCEND, and ASPREE trials re-evaluated primary prevention — "
                "showing modest benefits outweighed by bleeding risks in low-risk individuals, "
                "leading to revised US Preventive Services Task Force guidelines limiting "
                "primary prevention use to ages 40–59 with ≥10% CVD risk.\n"
                "Regulatory approvals: FDA-approved for multiple indications since the "
                "early 20th century; modern cardiovascular indications formally approved "
                "through NDA supplements from the 1980s onward."
            ),
            sources=[Citation(source="DailyMed SPL — Aspirin", url="https://dailymed.nlm.nih.gov")],
        ),
    ),
)
