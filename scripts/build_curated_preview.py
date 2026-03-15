from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

ESMO_RAW_PATH = ROOT / "datasets" / "esmo" / "ESMO_Stage_IV_SqCC_10_Recommended_Treatments_NORMALIZED_v0.3.1_3layer.json"
PUBMED_RAW_PATH = ROOT / "datasets" / "pubmed" / "Test11.txt"

ESMO_CANONICAL_PATH = ROOT / "datasets" / "esmo" / "topics.curated.json"
PUBMED_CANONICAL_PATH = ROOT / "datasets" / "pubmed" / "evidence.curated.json"
FROZEN_CANONICAL_PATH = ROOT / "datasets" / "vignettes" / "frozen_pack.curated.json"
FROZEN_SAMPLE_PATH = ROOT / "datasets" / "vignettes" / "frozen_pack.sample.json"
DEMO_PRESETS_CANONICAL_PATH = ROOT / "datasets" / "vignettes" / "demo_presets.curated.json"
API_ESMO_CANONICAL_PATH = ROOT / "apps" / "api" / "datasets" / "esmo" / "topics.curated.json"
API_PUBMED_CANONICAL_PATH = ROOT / "apps" / "api" / "datasets" / "pubmed" / "evidence.curated.json"
API_FROZEN_CANONICAL_PATH = ROOT / "apps" / "api" / "datasets" / "vignettes" / "frozen_pack.curated.json"
API_FROZEN_SAMPLE_PATH = ROOT / "apps" / "api" / "datasets" / "vignettes" / "frozen_pack.sample.json"
API_DEMO_PRESETS_CANONICAL_PATH = ROOT / "apps" / "api" / "datasets" / "vignettes" / "demo_presets.curated.json"


TOPIC_CONFIG: dict[str, dict] = {
    "SQCC_IV_01": {
        "lineOfTherapy": ["first_line"],
        "biomarkerConditions": ["all_negative(EGFR,ALK,ROS1)", "PDL1Bucket>=ge50"],
        "topicInterventionTags": ["pd1", "ici", "immunotherapy-monotherapy"],
        "prerequisites": ["line_of_therapy:first-line"],
    },
    "SQCC_IV_02": {
        "lineOfTherapy": ["first_line"],
        "biomarkerConditions": ["all_negative(EGFR,ALK,ROS1)", "PDL1Bucket>=ge50"],
        "topicInterventionTags": ["pdl1", "ici", "immunotherapy-monotherapy"],
        "prerequisites": ["line_of_therapy:first-line"],
    },
    "SQCC_IV_03": {
        "lineOfTherapy": ["first_line"],
        "biomarkerConditions": ["all_negative(EGFR,ALK,ROS1)"],
        "topicInterventionTags": ["pd1", "ici", "chemo-ici", "platinum-doublet"],
        "prerequisites": ["line_of_therapy:first-line", "pdl1:any"],
    },
    "SQCC_IV_04": {
        "lineOfTherapy": ["first_line"],
        "biomarkerConditions": ["all_negative(EGFR,ALK,ROS1)"],
        "topicInterventionTags": ["pd1", "ctla4", "dual-ici", "chemo-ici", "platinum-doublet"],
        "prerequisites": ["line_of_therapy:first-line", "pdl1:any"],
    },
    "SQCC_IV_05": {
        "lineOfTherapy": ["first_line"],
        "biomarkerConditions": ["all_negative(EGFR,ALK,ROS1)", "PDL1Bucket>=1to49"],
        "topicInterventionTags": ["pd1", "ctla4", "dual-ici"],
        "prerequisites": ["line_of_therapy:first-line", "pdl1:ge1"],
    },
    "SQCC_IV_06": {
        "lineOfTherapy": ["first_line"],
        "biomarkerConditions": ["all_negative(EGFR,ALK,ROS1)", "PDL1Bucket<ge50"],
        "topicInterventionTags": ["chemotherapy", "platinum-doublet"],
        "prerequisites": ["line_of_therapy:first-line", "performance_status:2", "pdl1:lt50"],
    },
    "SQCC_IV_07": {
        "lineOfTherapy": ["first_line"],
        "biomarkerConditions": [],
        "topicInterventionTags": ["chemotherapy", "single-agent-chemo"],
        "prerequisites": ["line_of_therapy:first-line", "frailty:yes"],
    },
    "SQCC_IV_08": {
        "lineOfTherapy": ["second_line", "later_line"],
        "biomarkerConditions": [],
        "topicInterventionTags": ["pd1", "pdl1", "ici", "immunotherapy"],
        "prerequisites": ["line_of_therapy:second-line"],
    },
    "SQCC_IV_09": {
        "lineOfTherapy": ["second_line", "later_line"],
        "biomarkerConditions": [],
        "topicInterventionTags": ["antiangiogenic", "docetaxel", "chemotherapy"],
        "prerequisites": ["line_of_therapy:second-line"],
    },
    "SQCC_IV_10": {
        "lineOfTherapy": ["first_line"],
        "biomarkerConditions": ["any_positive(EGFR,ALK,ROS1,BRAF,RET,MET,EGFRExon20ins,KRAS,NTRK,HER2)"],
        "topicInterventionTags": [
            "egfr-targeted",
            "alk-targeted",
            "ros1-targeted",
            "braf-targeted",
            "ret-targeted",
            "met-targeted",
            "kras-targeted",
            "ntrk-targeted",
            "her2-targeted",
        ],
        "prerequisites": ["line_of_therapy:first-line", "oncogenic_driver:required"],
    },
}


PUBMED_OVERRIDES: dict[str, dict] = {
    "40118215": {
        "diseaseSetting": "metastatic",
        "histology": "all_nsclc",
        "lineOfTherapy": "first_line",
        "biomarkers": {"EGFR": "no", "ALK": "no", "ROS1": "no", "PDL1Bucket": "ge50"},
        "interventionTags": ["pd1", "ici", "immunotherapy-monotherapy", "cemiplimab"],
    },
    "40446626": {
        "diseaseSetting": "metastatic",
        "histology": "mixed",
        "lineOfTherapy": "first_line",
        "biomarkers": {"EGFR": "no", "ALK": "no", "ROS1": "no", "PDL1Bucket": "unspecified"},
        "interventionTags": ["pd1", "ctla4", "dual-ici", "chemo-ici", "platinum-doublet", "nivolumab", "ipilimumab"],
    },
    "40473437": {
        "diseaseSetting": "metastatic",
        "histology": "all_nsclc",
        "lineOfTherapy": "second_line",
        "biomarkers": {"EGFR": "yes", "ALK": "unspecified", "ROS1": "unspecified", "PDL1Bucket": "unspecified"},
        "interventionTags": ["trop2-adc", "docetaxel", "sacituzumab-tirumotecan"],
        "evidenceType": "phase3_rct",
    },
    "39622410": {
        "diseaseSetting": "metastatic",
        "histology": "all_nsclc",
        "lineOfTherapy": "first_line",
        "biomarkers": {"EGFR": "yes", "ALK": "unspecified", "ROS1": "unspecified", "PDL1Bucket": "unspecified"},
        "interventionTags": ["egfr-targeted", "egfr-tki", "antiangiogenic", "erlotinib", "ramucirumab"],
    },
    "40923969": {
        "diseaseSetting": "metastatic",
        "histology": "all_nsclc",
        "lineOfTherapy": "first_line",
        "biomarkers": {"EGFR": "yes", "ALK": "unspecified", "ROS1": "unspecified", "PDL1Bucket": "unspecified", "MET": "unspecified"},
        "interventionTags": ["supportive-care", "egfr-met-bispecific", "egfr-tki", "amivantamab", "lazertinib"],
        "evidenceType": "phase2_rct",
    },
    "40379995": {
        "diseaseSetting": "metastatic",
        "histology": "non_squamous",
        "lineOfTherapy": "first_line",
        "biomarkers": {"EGFR": "unspecified", "ALK": "unspecified", "ROS1": "unspecified", "PDL1Bucket": "unspecified"},
        "interventionTags": ["pdl1", "antiangiogenic", "chemo-ici", "platinum-doublet", "atezolizumab", "bevacizumab"],
    },
    "40897431": {
        "diseaseSetting": "mixed",
        "histology": "all_nsclc",
        "lineOfTherapy": "mixed",
        "biomarkers": {"EGFR": "yes", "ALK": "unspecified", "ROS1": "unspecified", "PDL1Bucket": "unspecified"},
        "interventionTags": ["egfr-targeted", "egfr-tki", "antiangiogenic"],
        "evidenceType": "systematic_review",
    },
    "40617394": {
        "diseaseSetting": "metastatic",
        "histology": "all_nsclc",
        "lineOfTherapy": "first_line",
        "biomarkers": {"EGFR": "yes", "ALK": "unspecified", "ROS1": "unspecified", "PDL1Bucket": "unspecified"},
        "interventionTags": ["egfr-targeted", "egfr-tki", "lazertinib", "osimertinib"],
    },
    "40516821": {
        "diseaseSetting": "metastatic",
        "histology": "all_nsclc",
        "lineOfTherapy": "later_line",
        "biomarkers": {"EGFR": "yes", "ALK": "unspecified", "ROS1": "unspecified", "PDL1Bucket": "unspecified"},
        "interventionTags": ["trop2-adc", "datopotamab-deruxtecan"],
        "evidenceType": "phase2_rct",
    },
}


def _load_json(path: Path) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def build_topics() -> list[dict]:
    topics = _load_json(ESMO_RAW_PATH)
    canonical: list[dict] = []

    for item in topics:
        topic_id = item["Topic_ID"]
        config = TOPIC_CONFIG[topic_id]
        notes = [item["Guideline_Excerpt_Short"], item["Applicability_Rules_in_plain_text"]]
        canonical.append(
            {
                "topicId": topic_id,
                "topicTitle": item["Title"],
                "topicApplicability": {
                    "diseaseSetting": ["metastatic"],
                    "histology": ["squamous"],
                    "lineOfTherapy": config["lineOfTherapy"],
                    "biomarkerConditions": config["biomarkerConditions"],
                },
                "topicInterventionTags": config["topicInterventionTags"],
                "guidelineStance": "recommend",
                "stanceNotes": " | ".join(notes),
                "prerequisites": config["prerequisites"] + [f"source_biomarkers:{item['Biomarkers_Required']}"],
            }
        )

    return canonical


def infer_evidence_type(publication_type: str) -> str:
    normalized = publication_type.lower()
    if "systematic review" in normalized or "network meta-analysis" in normalized:
        return "systematic_review"
    if "phase iii" in normalized:
        return "phase3_rct"
    if "phase ii" in normalized and "phase iii" not in normalized:
        return "phase2_rct"
    if "randomized controlled trial" in normalized:
        return "phase3_rct"
    return "prospective_obs"


def infer_source_category(journal_title: str) -> str:
    normalized = journal_title.lower()
    high_impact_titles = {
        "bmj (clinical research ed.)",
        "nature medicine",
        "journal of thoracic oncology : official publication of the international association for the study of lung cancer",
    }
    if normalized in high_impact_titles:
        return "high_impact_journal"
    return "specialty_journal"


def parse_int(value: str) -> int | None:
    cleaned = value.strip()
    if not cleaned or cleaned == "unspecified":
        return None
    return int(cleaned)


def relevant_n(row: dict) -> int | None:
    direct_total = parse_int(row["sample_size_total"])
    if direct_total is not None:
        return direct_total

    arm_sizes = [
        parse_int(row["sample_size_arm_cemiplimab"]),
        parse_int(row["sample_size_arm_chemotherapy"]),
        parse_int(row["sample_size_arm_nivolumab"]),
    ]
    numeric_sizes = [size for size in arm_sizes if size is not None]
    if not numeric_sizes:
        return None
    return sum(numeric_sizes)


def build_evidence() -> list[dict]:
    with PUBMED_RAW_PATH.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))

    canonical: list[dict] = []
    for row in rows:
        pmid = row["pmid"]
        override = PUBMED_OVERRIDES[pmid]
        evidence_type = override.get("evidenceType", infer_evidence_type(row["publication_type"]))
        canonical.append(
            {
                "evidenceId": f"PMID-{pmid}",
                "title": row["title"],
                "abstract": row["abstract"].strip() or None,
                "journalTitle": row["journal_title"].strip() or None,
                "publicationYear": parse_int(row["pub_year"]),
                "evidenceType": evidence_type,
                "relevantN": relevant_n(row),
                "sourceCategory": infer_source_category(row["journal_title"]),
                "populationTags": {
                        "disease": "NSCLC",
                        "diseaseSetting": override["diseaseSetting"],
                        "histology": override["histology"],
                        "lineOfTherapy": override["lineOfTherapy"],
                        "biomarkers": override["biomarkers"],
                    },
                "interventionTags": override["interventionTags"],
                "outcomeTags": [tag.strip() for tag in row["outcome_tags"].split(",") if tag.strip() and tag.strip() != "unspecified"],
            }
        )

    return canonical


def load_canonical_frozen_pack() -> dict:
    return json.loads(FROZEN_CANONICAL_PATH.read_text(encoding="utf-8"))


def load_canonical_demo_presets() -> dict:
    return json.loads(DEMO_PRESETS_CANONICAL_PATH.read_text(encoding="utf-8"))


def main() -> None:
    topics = build_topics()
    evidence = build_evidence()
    frozen_pack = load_canonical_frozen_pack()
    demo_presets = load_canonical_demo_presets()

    _write_json(ESMO_CANONICAL_PATH, topics)
    _write_json(PUBMED_CANONICAL_PATH, evidence)
    _write_json(FROZEN_SAMPLE_PATH, frozen_pack)
    _write_json(API_ESMO_CANONICAL_PATH, topics)
    _write_json(API_PUBMED_CANONICAL_PATH, evidence)
    _write_json(API_FROZEN_CANONICAL_PATH, frozen_pack)
    _write_json(API_FROZEN_SAMPLE_PATH, frozen_pack)
    _write_json(API_DEMO_PRESETS_CANONICAL_PATH, demo_presets)

    print(f"Wrote {len(topics)} curated ESMO topics -> {ESMO_CANONICAL_PATH.relative_to(ROOT)}")
    print(f"Wrote {len(evidence)} curated PubMed records -> {PUBMED_CANONICAL_PATH.relative_to(ROOT)}")
    print(f"Mirrored canonical frozen pack -> {FROZEN_SAMPLE_PATH.relative_to(ROOT)}")
    print(f"Mirrored canonical demo presets -> {API_DEMO_PRESETS_CANONICAL_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
