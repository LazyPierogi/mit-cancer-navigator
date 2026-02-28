from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class BiomarkersModel(BaseModel):
    EGFR: Literal["yes", "no"]
    ALK: Literal["yes", "no"]
    ROS1: Literal["yes", "no"]
    PDL1Bucket: Literal["lt1", "1to49", "ge50"]


class VignetteInputModel(BaseModel):
    cancerType: Literal["NSCLC"] = "NSCLC"
    diseaseSetting: Literal["early", "locally_advanced", "metastatic"]
    histology: Literal["adenocarcinoma", "squamous"]
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

