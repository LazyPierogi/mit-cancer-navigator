from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class BiomarkersModel(BaseModel):
    EGFR: Literal["yes", "no", "unspecified"] = "unspecified"
    ALK: Literal["yes", "no", "unspecified"] = "unspecified"
    ROS1: Literal["yes", "no", "unspecified"] = "unspecified"
    PDL1Bucket: Literal["lt1", "1to49", "ge50", "unspecified"] = "unspecified"
    BRAF: Literal["yes", "no", "unspecified"] = "unspecified"
    RET: Literal["yes", "no", "unspecified"] = "unspecified"
    MET: Literal["yes", "no", "unspecified"] = "unspecified"
    KRAS: Literal["yes", "no", "unspecified"] = "unspecified"
    NTRK: Literal["yes", "no", "unspecified"] = "unspecified"
    HER2: Literal["yes", "no", "unspecified"] = "unspecified"
    EGFRExon20ins: Literal["yes", "no", "unspecified"] = "unspecified"


class VignetteInputModel(BaseModel):
    cancerType: Literal["NSCLC"] = "NSCLC"
    diseaseSetting: Literal["early", "locally_advanced", "metastatic"]
    histology: Literal["adenocarcinoma", "squamous", "non_squamous"]
    lineOfTherapy: Literal["first_line", "second_line", "later_line", "mixed", "unspecified"] = "unspecified"
    performanceStatus: Literal["0", "1", "2", "3", "4"]
    biomarkers: BiomarkersModel


class CitationRefModel(BaseModel):
    sourceId: str
    title: str
    year: int | None = None


class ScoreBreakdownModel(BaseModel):
    evidenceStrength: int
    datasetRobustness: int
    sourceCredibility: int
    recency: int


class TopEvidenceItemModel(BaseModel):
    rank: int
    evidenceId: str
    title: str
    publicationYear: int | None = None
    ersTotal: int
    ersBreakdown: ScoreBreakdownModel
    mappedTopicId: str | None = None
    mappedTopicTitle: str | None = None
    mappingLabel: Literal["aligned", "guideline_silent", "conflict"]
    applicabilityNote: str
    citations: list[CitationRefModel]


class SecondaryReferenceModel(BaseModel):
    evidenceId: str
    exclusionReasons: list[str]


class RunInfoModel(BaseModel):
    id: str
    status: Literal["queued", "running", "completed", "failed"]
    rulesetVersion: str
    corpusVersion: str
    createdAt: datetime
    latencyMs: int | None = None


class AnalyzeRunResponseModel(BaseModel):
    run: RunInfoModel
    topEvidence: list[TopEvidenceItemModel]
    secondaryReferences: list[SecondaryReferenceModel]
    uncertaintyFlags: list[str]
    safetyFooterKey: str
    traceId: str


class TracePayloadModel(BaseModel):
    traceId: str
    runId: str
    inputSchemaVersion: str
    rulesetVersion: str
    corpusVersion: str
    gateCandidateCount: int
    eligibleCount: int
    topEvidenceCount: int
    secondaryCount: int
    uncertaintyFlags: list[str]
    safetyFooterKey: str


class GovernancePolicyModel(BaseModel):
    scope: str
    frozenLabelVocabulary: list[str]
    hardStops: list[str]
    softReviewTriggers: list[str]
    safetyBoundaries: list[str]


class ImportRequestModel(BaseModel):
    path: str | None = None


class ValidationIssueModel(BaseModel):
    severity: str
    code: str
    message: str
    record_id: str | None = None


class ValidationReportModel(BaseModel):
    datasetKind: str
    datasetShape: str
    path: str
    errorCount: int
    warningCount: int
    info: list[str]
    errors: list[ValidationIssueModel]
    warnings: list[ValidationIssueModel]


class ImportBatchModel(BaseModel):
    batchId: str
    datasetKind: str
    datasetShape: str
    sourcePath: str
    status: str
    recordCount: int
    importedCount: int
    errorCount: int
    warningCount: int
    validation: ValidationReportModel
    notes: list[str]
    createdAt: datetime


class ImportSummaryKindModel(BaseModel):
    batchId: str
    status: str
    recordCount: int
    importedCount: int
    warningCount: int
    errorCount: int
    createdAt: datetime


class RuntimeSourcesModel(BaseModel):
    topics: Literal["db_imported", "file_fallback"]
    evidence: Literal["db_imported", "file_fallback"]


class ImportSummaryModel(BaseModel):
    activeTopics: int
    activeEvidenceStudies: int
    importBatchCount: int
    latestBatchId: str | None = None
    latestBatchStatus: str | None = None
    latestByKind: dict[str, ImportSummaryKindModel]
    runtimeSources: RuntimeSourcesModel


class EvalMetricModel(BaseModel):
    name: str
    value: float | int
    target: str | None = None


class EvalResultModel(BaseModel):
    evalRunId: str
    packId: str
    layer1: dict[str, bool]
    layer2Metrics: list[EvalMetricModel]
    notes: list[str] = Field(default_factory=list)
