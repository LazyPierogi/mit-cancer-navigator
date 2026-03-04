from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]

ESMO_RAW_REQUIRED_FIELDS = {
    "Topic_ID",
    "Title",
    "Disease_setting",
    "Line_of_Therapy",
    "Histology",
    "Biomarkers_Required",
    "Intervention_Tags",
    "Stance",
    "Applicability_Rules_in_plain_text",
    "Guideline_Excerpt_Short",
}

ESMO_CANONICAL_REQUIRED_FIELDS = {
    "topicId",
    "topicTitle",
    "topicApplicability",
    "topicInterventionTags",
    "guidelineStance",
}

PUBMED_RAW_REQUIRED_FIELDS = {
    "pmid",
    "title",
    "abstract",
    "pub_year",
    "publication_type",
    "journal_title",
    "sample_size_total",
    "disease_setting_tag",
    "line_of_therapy_tag",
    "histology_tag",
    "EGFR_tag",
    "ALK_tag",
    "ROS1_tag",
    "PDL1_rule_tag",
    "intervention_tags",
    "outcome_tags",
    "notes",
}

PUBMED_RAW_V2_REQUIRED_FIELDS = {
    "pmid",
    "title",
    "abstract",
    "publicationYear",
    "publicationType",
    "journalTitle",
    "evidenceType",
    "diseaseSetting",
    "histology",
    "lineOfTherapy",
    "biomarkers",
    "interventionTags",
    "outcomeTags",
    "relevantN",
}

PUBMED_CANONICAL_REQUIRED_FIELDS = {
    "evidenceId",
    "title",
    "publicationYear",
    "evidenceType",
    "populationTags",
    "interventionTags",
    "outcomeTags",
}

CANONICAL_DISEASE_SETTINGS = {"early", "locally_advanced", "metastatic", "mixed", "unspecified"}
CANONICAL_HISTOLOGY = {"adenocarcinoma", "squamous", "non_squamous", "all_nsclc", "mixed", "unspecified"}
CANONICAL_LINE_OF_THERAPY = {"first_line", "second_line", "later_line", "mixed", "unspecified"}
CANONICAL_STANCE = {"recommend", "conditional", "do_not_recommend", "not_covered"}
CANONICAL_EVIDENCE_TYPES = {
    "guideline",
    "systematic_review",
    "phase3_rct",
    "phase2_rct",
    "prospective_obs",
    "retrospective",
    "case_series",
    "expert_opinion",
}
CANONICAL_EVIDENCE_TYPE_ALIASES = {
    "randomized control trial": "phase3_rct",
    "randomized controlled trial": "phase3_rct",
    "systematic review": "systematic_review",
}
CANONICAL_BIOMARKER_FLAGS = {"yes", "no", "unspecified"}
CANONICAL_PDL1_BUCKETS = {"lt1", "1to49", "ge50", "unspecified"}
RAW_PDL1_BUCKETS = CANONICAL_PDL1_BUCKETS | {"any"}
CANONICAL_BIOMARKER_KEYS = {
    "EGFR",
    "ALK",
    "ROS1",
    "PDL1Bucket",
    "BRAF",
    "RET",
    "MET",
    "KRAS",
    "NTRK",
    "HER2",
    "EGFRExon20ins",
}
CANONICAL_INTERVENTION_TAG_RE = re.compile(r"^[a-z0-9][a-z0-9\-]*$")
RAW_BIOMARKER_RED_FLAGS = {"positive", "negative"}
RAW_PDL1_FLAG_KEYS = {"PDL1_ge50", "PDL1_1to49", "PDL1_lt1", "PDL1_any"}
RAW_PDL1_FREE_TEXT_THRESHOLD = 80
MULTI_SCENARIO_RE = re.compile(r"(first[- ]line.*second[- ]line|second[- ]line.*first[- ]line)", re.IGNORECASE)
STRICT_MVP_PUBMED_EVIDENCE_TYPES = {"phase3_rct", "systematic_review"}


@dataclass(slots=True)
class ValidationIssue:
    severity: str
    code: str
    message: str
    record_id: str | None = None


@dataclass(slots=True)
class ValidationReport:
    dataset_kind: str
    dataset_shape: str
    path: str
    errors: list[ValidationIssue] = field(default_factory=list)
    warnings: list[ValidationIssue] = field(default_factory=list)
    info: list[str] = field(default_factory=list)

    def add(self, severity: str, code: str, message: str, record_id: str | None = None) -> None:
        issue = ValidationIssue(severity=severity, code=code, message=message, record_id=record_id)
        if severity == "error":
            self.errors.append(issue)
        else:
            self.warnings.append(issue)

    @property
    def error_count(self) -> int:
        return len(self.errors)

    @property
    def warning_count(self) -> int:
        return len(self.warnings)

    def to_dict(self) -> dict[str, Any]:
        return {
            "datasetKind": self.dataset_kind,
            "datasetShape": self.dataset_shape,
            "path": self.path,
            "errorCount": self.error_count,
            "warningCount": self.warning_count,
            "info": self.info,
            "errors": [asdict(issue) for issue in self.errors],
            "warnings": [asdict(issue) for issue in self.warnings],
        }


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _has_missing_fields(record: dict[str, Any], required_fields: set[str]) -> set[str]:
    return required_fields - set(record.keys())


def _validate_json_list(payload: Any, report: ValidationReport) -> list[dict[str, Any]]:
    if not isinstance(payload, list):
        report.add("error", "not_a_list", "Expected the file payload to be a JSON array.")
        return []
    if not payload:
        report.add("error", "empty_payload", "Dataset is empty.")
        return []
    for index, item in enumerate(payload):
        if not isinstance(item, dict):
            report.add("error", "non_object_row", f"Row {index} is not a JSON object.")
    return [item for item in payload if isinstance(item, dict)]


def _validate_non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _validate_esmo_raw(records: list[dict[str, Any]], report: ValidationReport) -> None:
    seen_ids: set[str] = set()
    for item in records:
        record_id = str(item.get("Topic_ID", "<missing>"))
        missing = _has_missing_fields(item, ESMO_RAW_REQUIRED_FIELDS)
        if missing:
            report.add("error", "missing_required_fields", f"Missing raw ESMO fields: {sorted(missing)}", record_id)
            continue

        if record_id in seen_ids:
            report.add("error", "duplicate_topic_id", "Duplicate Topic_ID.", record_id)
        seen_ids.add(record_id)

        for field in ("Title", "Disease_setting", "Line_of_Therapy", "Histology", "Biomarkers_Required", "Stance"):
            if not _validate_non_empty_string(item.get(field)):
                report.add("error", "empty_required_value", f"Field `{field}` must be a non-empty string.", record_id)

        if MULTI_SCENARIO_RE.search(item["Title"]) or MULTI_SCENARIO_RE.search(item["Line_of_Therapy"]):
            report.add("warning", "mixed_scenarios", "Looks like multiple therapy lines may be mixed into one row.", record_id)

        if not isinstance(item.get("Intervention_Tags"), list) or not item["Intervention_Tags"]:
            report.add("error", "invalid_intervention_tags", "`Intervention_Tags` must be a non-empty list.", record_id)
        else:
            for tag in item["Intervention_Tags"]:
                if not _validate_non_empty_string(tag):
                    report.add("warning", "blank_intervention_tag", "Found an empty intervention tag.", record_id)

        if item.get("Normalized_Tags_v0.3.1_3layer") == []:
            report.add(
                "warning",
                "missing_3layer_tags",
                "Normalized 3-layer tags are empty; this usually means the row still needs structured normalization.",
                record_id,
            )

        stance = str(item["Stance"]).strip().lower()
        if stance not in {"recommended", "conditional", "do not recommend", "not covered"}:
            report.add("warning", "nonstandard_stance", f"Unexpected raw stance value `{item['Stance']}`.", record_id)


def _validate_biomarker_rules(rules: Any, report: ValidationReport, record_id: str) -> None:
    if not isinstance(rules, list):
        report.add("error", "invalid_biomarker_conditions", "`biomarkerConditions` must be a list.", record_id)
        return
    for condition in rules:
        if not _validate_non_empty_string(condition):
            report.add("warning", "blank_biomarker_condition", "Blank biomarker condition found.", record_id)


def _validate_esmo_canonical(records: list[dict[str, Any]], report: ValidationReport) -> None:
    seen_ids: set[str] = set()
    for item in records:
        record_id = str(item.get("topicId", "<missing>"))
        missing = _has_missing_fields(item, ESMO_CANONICAL_REQUIRED_FIELDS)
        if missing:
            report.add("error", "missing_required_fields", f"Missing canonical ESMO fields: {sorted(missing)}", record_id)
            continue

        if record_id in seen_ids:
            report.add("error", "duplicate_topic_id", "Duplicate topicId.", record_id)
        seen_ids.add(record_id)

        applicability = item.get("topicApplicability")
        if not isinstance(applicability, dict):
            report.add("error", "invalid_topic_applicability", "`topicApplicability` must be an object.", record_id)
            continue

        disease_setting = applicability.get("diseaseSetting", [])
        histology = applicability.get("histology", [])
        line_of_therapy = applicability.get("lineOfTherapy", [])

        for value in disease_setting:
            if value not in CANONICAL_DISEASE_SETTINGS:
                report.add("error", "invalid_disease_setting", f"Unknown diseaseSetting `{value}`.", record_id)
        for value in histology:
            if value not in CANONICAL_HISTOLOGY:
                report.add("error", "invalid_histology", f"Unknown histology `{value}`.", record_id)
        for value in line_of_therapy:
            if value not in CANONICAL_LINE_OF_THERAPY:
                report.add("error", "invalid_line_of_therapy", f"Unknown lineOfTherapy `{value}`.", record_id)

        _validate_biomarker_rules(applicability.get("biomarkerConditions", []), report, record_id)

        stance = item.get("guidelineStance")
        if stance not in CANONICAL_STANCE:
            report.add("error", "invalid_guideline_stance", f"Unknown guidelineStance `{stance}`.", record_id)

        tags = item.get("topicInterventionTags")
        if not isinstance(tags, list) or not tags:
            report.add("error", "invalid_intervention_tags", "`topicInterventionTags` must be a non-empty list.", record_id)
        else:
            for tag in tags:
                if not isinstance(tag, str) or not CANONICAL_INTERVENTION_TAG_RE.match(tag):
                    report.add("warning", "noncanonical_intervention_tag", f"Intervention tag `{tag}` is not normalized.", record_id)


def _split_csv_values(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def _normalize_token(value: str) -> str:
    normalized = value.strip().lower().replace("-", "_").replace(" ", "_")
    while "__" in normalized:
        normalized = normalized.replace("__", "_")
    return normalized


def _parse_list_cell(value: str) -> list[str]:
    raw = value.strip()
    if not raw:
        return []

    if raw.startswith("[") and raw.endswith("]"):
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, list):
                return [str(item).strip() for item in parsed if str(item).strip()]
        except json.JSONDecodeError:
            pass

    return [item.strip() for item in raw.split(",") if item.strip()]


def _parse_biomarkers_cell(value: str) -> dict[str, str] | None:
    raw = value.strip()
    if not raw:
        return {}

    if raw.startswith("{") and raw.endswith("}"):
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, dict):
                return {str(key).strip(): str(item).strip() for key, item in parsed.items()}
        except json.JSONDecodeError:
            return None

    if "=" not in raw:
        return None

    payload: dict[str, str] = {}
    for chunk in raw.split(","):
        part = chunk.strip()
        if not part:
            continue
        if "=" not in part:
            return None
        key, item = part.split("=", 1)
        payload[key.strip()] = item.strip()
    return payload


def _validate_pubmed_raw_v2(
    item: dict[str, str], report: ValidationReport, seen_ids: set[str], *, strict_mvp_pubmed: bool = False
) -> None:
    record_id = item.get("pmid") or "<missing>"
    missing = _has_missing_fields(item, PUBMED_RAW_V2_REQUIRED_FIELDS)
    if missing:
        report.add("error", "missing_required_fields", f"Missing raw PubMed v2 fields: {sorted(missing)}", record_id)
        return

    if record_id in seen_ids:
        report.add("error", "duplicate_pmid", "Duplicate pmid.", record_id)
    seen_ids.add(record_id)

    for field in ("title", "abstract", "publicationYear", "publicationType", "journalTitle", "evidenceType"):
        if not _validate_non_empty_string(item.get(field)):
            report.add("error", "empty_required_value", f"Field `{field}` must be a non-empty string.", record_id)

    publication_year = item.get("publicationYear", "").strip()
    if publication_year and publication_year not in {"unspecified", "null"} and not publication_year.isdigit():
        report.add("error", "invalid_publication_year", f"publicationYear `{publication_year}` is not numeric.", record_id)

    evidence_type = _normalize_token(item.get("evidenceType", ""))
    effective_evidence_type = evidence_type
    if evidence_type not in CANONICAL_EVIDENCE_TYPES:
        mapped = CANONICAL_EVIDENCE_TYPE_ALIASES.get(item.get("evidenceType", "").strip().lower())
        if mapped is None:
            report.add(
                "error",
                "invalid_evidence_type",
                f"evidenceType `{item.get('evidenceType')}` is not normalized to canonical tokens.",
                record_id,
            )
        else:
            effective_evidence_type = mapped
            report.add(
                "error" if strict_mvp_pubmed else "warning",
                "noncanonical_evidence_type_alias",
                f"evidenceType `{item.get('evidenceType')}` should be sent as `{mapped}`.",
                record_id,
            )

    if strict_mvp_pubmed and effective_evidence_type not in STRICT_MVP_PUBMED_EVIDENCE_TYPES:
        report.add(
            "error",
            "evidence_type_outside_mvp_scope",
            f"evidenceType `{effective_evidence_type}` is outside MVP scope {sorted(STRICT_MVP_PUBMED_EVIDENCE_TYPES)}.",
            record_id,
        )

    for field, allowed in (
        ("diseaseSetting", CANONICAL_DISEASE_SETTINGS),
        ("histology", CANONICAL_HISTOLOGY),
        ("lineOfTherapy", CANONICAL_LINE_OF_THERAPY),
    ):
        raw_value = item.get(field, "").strip()
        if not raw_value:
            report.add("error", "empty_required_value", f"Field `{field}` must be a non-empty string.", record_id)
            continue

        if "," in raw_value:
            normalized = "mixed"
        else:
            normalized = _normalize_token(raw_value)
        if normalized not in allowed:
            report.add("error", f"invalid_{field}", f"Unknown {field} `{raw_value}`.", record_id)

    biomarkers = _parse_biomarkers_cell(item.get("biomarkers", ""))
    if biomarkers is None:
        report.add("error", "invalid_biomarkers_payload", "`biomarkers` cannot be parsed.", record_id)
    else:
        pdl1_flag_values: dict[str, str] = {}
        pdl1_bucket_seen = False
        for key, raw_value in biomarkers.items():
            value = _normalize_token(raw_value)
            if key in RAW_PDL1_FLAG_KEYS:
                pdl1_flag_values[key] = value
                if value not in CANONICAL_BIOMARKER_FLAGS:
                    report.add("error", "invalid_biomarker_flag", f"Unknown value `{raw_value}` for `{key}`.", record_id)
                continue

            if key == "PDL1Bucket":
                pdl1_bucket_seen = True
                if value not in RAW_PDL1_BUCKETS:
                    report.add("error", "invalid_pdl1_bucket", f"Unknown PDL1Bucket `{raw_value}`.", record_id)
                continue

            if key not in CANONICAL_BIOMARKER_KEYS:
                report.add("warning", "unknown_biomarker_key", f"Unknown biomarker key `{key}`.", record_id)
                continue
            if value not in CANONICAL_BIOMARKER_FLAGS:
                report.add("error", "invalid_biomarker_flag", f"Unknown biomarker value `{raw_value}` for `{key}`.", record_id)

        if pdl1_flag_values and pdl1_bucket_seen:
            report.add(
                "warning",
                "mixed_pdl1_encodings",
                "Found both `PDL1Bucket` and `PDL1_*` flags. Prefer only `PDL1Bucket`.",
                record_id,
            )
        if pdl1_flag_values:
            positives = [key for key, val in pdl1_flag_values.items() if val == "yes"]
            if len(positives) > 1:
                report.add(
                    "error",
                    "ambiguous_pdl1_flags",
                    f"Multiple PD-L1 flags are marked `yes`: {sorted(positives)}.",
                    record_id,
                )

    for field, warning_code in (("interventionTags", "missing_intervention_tags"), ("outcomeTags", "missing_outcome_tags")):
        values = _parse_list_cell(item.get(field, ""))
        if not values or values == ["unspecified"]:
            report.add("error" if strict_mvp_pubmed and field == "interventionTags" else "warning", warning_code, f"{field} are missing or unspecified.", record_id)


def _validate_pubmed_raw(records: list[dict[str, str]], report: ValidationReport, *, strict_mvp_pubmed: bool = False) -> None:
    seen_ids: set[str] = set()
    for item in records:
        if not _has_missing_fields(item, PUBMED_RAW_V2_REQUIRED_FIELDS):
            _validate_pubmed_raw_v2(item, report, seen_ids, strict_mvp_pubmed=strict_mvp_pubmed)
            continue

        record_id = item.get("pmid") or "<missing>"
        missing = _has_missing_fields(item, PUBMED_RAW_REQUIRED_FIELDS)
        if missing:
            report.add("error", "missing_required_fields", f"Missing raw PubMed fields: {sorted(missing)}", record_id)
            continue

        if record_id in seen_ids:
            report.add("error", "duplicate_pmid", "Duplicate pmid.", record_id)
        seen_ids.add(record_id)

        for field in ("title", "abstract", "pub_year", "publication_type", "journal_title"):
            if not _validate_non_empty_string(item.get(field)):
                report.add("error", "empty_required_value", f"Field `{field}` must be a non-empty string.", record_id)

        if not str(item["pub_year"]).isdigit():
            report.add("error", "invalid_publication_year", f"pub_year `{item['pub_year']}` is not numeric.", record_id)

        for field in ("sample_size_total", "sample_size_arm_cemiplimab", "sample_size_arm_chemotherapy", "sample_size_arm_nivolumab"):
            raw_value = item.get(field, "").strip()
            if raw_value not in {"", "unspecified"} and not raw_value.isdigit():
                report.add("error", "invalid_sample_size", f"Field `{field}` must be numeric or `unspecified`.", record_id)

        for field in ("EGFR_tag", "ALK_tag", "ROS1_tag"):
            raw_value = item.get(field, "").strip().lower()
            if raw_value in RAW_BIOMARKER_RED_FLAGS:
                report.add(
                    "warning",
                    "ambiguous_biomarker_flag",
                    f"`{field}` uses `{item[field]}`. Use cohort meaning, not entity mention shortcuts.",
                    record_id,
                )

        pdl1_rule = item.get("PDL1_rule_tag", "").strip()
        if len(pdl1_rule) > RAW_PDL1_FREE_TEXT_THRESHOLD:
            report.add(
                "warning",
                "free_text_pdl1_rule",
                "PDL1_rule_tag looks like long free text. Prefer a structured bucket such as lt1 / 1to49 / ge50.",
                record_id,
            )

        if item.get("intervention_tags", "").strip() in {"", "unspecified"}:
            report.add("warning", "missing_intervention_tags", "Intervention tags are missing or unspecified.", record_id)
        if item.get("outcome_tags", "").strip() in {"", "unspecified"}:
            report.add("warning", "missing_outcome_tags", "Outcome tags are missing or unspecified.", record_id)

        if MULTI_SCENARIO_RE.search(item.get("line_of_therapy_tag", "")):
            report.add("warning", "mixed_scenarios", "line_of_therapy_tag may be mixing multiple therapy lines.", record_id)


def _validate_pubmed_canonical(records: list[dict[str, Any]], report: ValidationReport) -> None:
    seen_ids: set[str] = set()
    for item in records:
        record_id = str(item.get("evidenceId", "<missing>"))
        missing = _has_missing_fields(item, PUBMED_CANONICAL_REQUIRED_FIELDS)
        if missing:
            report.add("error", "missing_required_fields", f"Missing canonical PubMed fields: {sorted(missing)}", record_id)
            continue

        if record_id in seen_ids:
            report.add("error", "duplicate_evidence_id", "Duplicate evidenceId.", record_id)
        seen_ids.add(record_id)

        evidence_type = item.get("evidenceType")
        if evidence_type not in CANONICAL_EVIDENCE_TYPES:
            report.add("error", "invalid_evidence_type", f"Unknown evidenceType `{evidence_type}`.", record_id)

        population_tags = item.get("populationTags")
        if not isinstance(population_tags, dict):
            report.add("error", "invalid_population_tags", "`populationTags` must be an object.", record_id)
            continue

        disease_setting = population_tags.get("diseaseSetting")
        histology = population_tags.get("histology")
        line_of_therapy = population_tags.get("lineOfTherapy", "unspecified")

        if disease_setting not in CANONICAL_DISEASE_SETTINGS:
            report.add("error", "invalid_disease_setting", f"Unknown diseaseSetting `{disease_setting}`.", record_id)
        if histology not in CANONICAL_HISTOLOGY:
            report.add("error", "invalid_histology", f"Unknown histology `{histology}`.", record_id)
        if line_of_therapy not in CANONICAL_LINE_OF_THERAPY:
            report.add("error", "invalid_line_of_therapy", f"Unknown lineOfTherapy `{line_of_therapy}`.", record_id)

        biomarkers = population_tags.get("biomarkers", {})
        if not isinstance(biomarkers, dict):
            report.add("error", "invalid_biomarkers", "`populationTags.biomarkers` must be an object.", record_id)
        else:
            for key, value in biomarkers.items():
                if key not in CANONICAL_BIOMARKER_KEYS:
                    report.add("warning", "unknown_biomarker_key", f"Unknown biomarker key `{key}`.", record_id)
                    continue
                if key == "PDL1Bucket":
                    if value not in CANONICAL_PDL1_BUCKETS:
                        report.add("error", "invalid_pdl1_bucket", f"Unknown PDL1Bucket `{value}`.", record_id)
                elif value not in CANONICAL_BIOMARKER_FLAGS:
                    report.add("error", "invalid_biomarker_flag", f"Unknown biomarker value `{value}` for `{key}`.", record_id)

        tags = item.get("interventionTags")
        if not isinstance(tags, list) or not tags:
            report.add("error", "invalid_intervention_tags", "`interventionTags` must be a non-empty list.", record_id)
        else:
            for tag in tags:
                if not isinstance(tag, str) or not CANONICAL_INTERVENTION_TAG_RE.match(tag):
                    report.add("warning", "noncanonical_intervention_tag", f"Intervention tag `{tag}` is not normalized.", record_id)

        outcome_tags = item.get("outcomeTags")
        if not isinstance(outcome_tags, list) or not outcome_tags:
            report.add("warning", "missing_outcome_tags", "`outcomeTags` should be a non-empty list.", record_id)


def _detect_dataset_shape(path: Path) -> tuple[str, list[dict[str, Any]]]:
    if path.suffix.lower() == ".csv" or path.suffix.lower() == ".txt":
        records = _read_csv(path)
        return "raw", records

    payload = _read_json(path)
    records = _validate_json_list(payload, ValidationReport("unknown", "unknown", str(path)))
    if records and "Topic_ID" in records[0]:
        return "raw", records
    return "canonical", records


def validate_dataset(path: Path, dataset_kind: str, *, strict_mvp_pubmed: bool = False) -> ValidationReport:
    if not path.exists():
        report = ValidationReport(dataset_kind=dataset_kind, dataset_shape="missing", path=str(path))
        report.add("error", "file_not_found", "Dataset path does not exist.")
        return report

    dataset_shape, records = _detect_dataset_shape(path)
    report = ValidationReport(dataset_kind=dataset_kind, dataset_shape=dataset_shape, path=str(path))

    if path.suffix.lower() == ".json":
        records = _validate_json_list(_read_json(path), report)
    elif path.suffix.lower() in {".csv", ".txt"}:
        records = _read_csv(path)
        if not records:
            report.add("error", "empty_payload", "Dataset is empty.")
            return report
    else:
        report.add("error", "unsupported_file_type", f"Unsupported file type `{path.suffix}`.")
        return report

    if dataset_kind == "esmo":
        if dataset_shape == "raw":
            _validate_esmo_raw(records, report)
        else:
            _validate_esmo_canonical(records, report)
    elif dataset_kind == "pubmed":
        if dataset_shape == "raw":
            _validate_pubmed_raw(records, report, strict_mvp_pubmed=strict_mvp_pubmed)
        else:
            _validate_pubmed_canonical(records, report)
    else:
        report.add("error", "unknown_dataset_kind", f"Unknown dataset kind `{dataset_kind}`.")

    report.info.append(f"Validated {len(records)} records.")
    return report


def _default_paths(root: Path) -> list[tuple[str, Path]]:
    return [
        ("esmo", root / "datasets" / "esmo" / "ESMO_Stage_IV_SqCC_10_Recommended_Treatments_NORMALIZED_v0.3.1_3layer.json"),
        ("pubmed", root / "datasets" / "pubmed" / "Test11.txt"),
        ("esmo", root / "datasets" / "esmo" / "topics.curated.json"),
        ("pubmed", root / "datasets" / "pubmed" / "evidence.curated.json"),
    ]


def _print_text_report(report: ValidationReport) -> None:
    print(f"[{report.dataset_kind.upper()}] {report.path}")
    print(f"shape: {report.dataset_shape}")
    print(f"errors: {report.error_count} | warnings: {report.warning_count}")
    for info_line in report.info:
        print(f"info: {info_line}")

    if report.errors:
        print("errors:")
        for issue in report.errors:
            record = f" ({issue.record_id})" if issue.record_id else ""
            print(f"  - [{issue.code}]{record} {issue.message}")

    if report.warnings:
        print("warnings:")
        for issue in report.warnings:
            record = f" ({issue.record_id})" if issue.record_id else ""
            print(f"  - [{issue.code}]{record} {issue.message}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate incoming ESMO / PubMed data drops.")
    parser.add_argument("--dataset", choices=["esmo", "pubmed"], help="Dataset kind to validate.")
    parser.add_argument("--path", help="Path to the dataset file.")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format.")
    parser.add_argument(
        "--current",
        action="store_true",
        help="Validate the current repo datasets (raw + curated preview) using built-in default paths.",
    )
    parser.add_argument(
        "--strict-warnings",
        action="store_true",
        help="Return a failing exit code if warnings are present.",
    )
    parser.add_argument(
        "--strict-mvp-pubmed",
        action="store_true",
        help="For PubMed raw validation, escalate non-MVP evidence types and missing intervention tags to errors.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    reports: list[ValidationReport] = []
    if args.current:
        reports = [
            validate_dataset(path, dataset_kind, strict_mvp_pubmed=args.strict_mvp_pubmed)
            for dataset_kind, path in _default_paths(ROOT)
        ]
    else:
        if not args.dataset or not args.path:
            print("Use --current or provide both --dataset and --path.", file=sys.stderr)
            return 2
        reports = [validate_dataset(Path(args.path), args.dataset, strict_mvp_pubmed=args.strict_mvp_pubmed)]

    if args.format == "json":
        print(json.dumps([report.to_dict() for report in reports], indent=2, ensure_ascii=True))
    else:
        for index, report in enumerate(reports):
            if index:
                print()
            _print_text_report(report)

    error_count = sum(report.error_count for report in reports)
    warning_count = sum(report.warning_count for report in reports)
    if error_count:
        return 1
    if args.strict_warnings and warning_count:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
