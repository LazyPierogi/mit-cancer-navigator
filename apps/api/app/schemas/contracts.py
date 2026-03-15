from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class BiomarkersModel(BaseModel):
    EGFR: Literal["yes", "no", "unspecified"] = "unspecified"
    ALK: Literal["yes", "no", "unspecified"] = "unspecified"
    ROS1: Literal["yes", "no", "unspecified"] = "unspecified"
    PDL1Bucket: Literal["lt1", "1to49", "ge50", "any", "unspecified"] = "unspecified"
    BRAF: Literal["yes", "no", "unspecified"] = "unspecified"
    RET: Literal["yes", "no", "unspecified"] = "unspecified"
    MET: Literal["yes", "no", "unspecified"] = "unspecified"
    KRAS: Literal["yes", "no", "unspecified"] = "unspecified"
    NTRK: Literal["yes", "no", "unspecified"] = "unspecified"
    HER2: Literal["yes", "no", "unspecified"] = "unspecified"
    EGFRExon20ins: Literal["yes", "no", "unspecified"] = "unspecified"


class ClinicalModifiersModel(BaseModel):
    brainMetastases: Literal["yes", "no", "unspecified"] = "unspecified"


class VignetteInputModel(BaseModel):
    cancerType: Literal["NSCLC"] = "NSCLC"
    diseaseSetting: Literal["early", "locally_advanced", "metastatic"]
    histology: Literal["adenocarcinoma", "squamous", "non_squamous"]
    lineOfTherapy: Literal["first_line", "second_line", "later_line", "adjuvant", "consolidation", "mixed", "unspecified"] = "unspecified"
    performanceStatus: Literal["0", "1", "2", "3", "4"]
    biomarkers: BiomarkersModel
    diseaseStage: Literal["stage_i", "stage_ii", "stage_iii", "stage_iv", "unspecified"] = "unspecified"
    resectabilityStatus: Literal["resected", "unresectable", "not_applicable", "unspecified"] = "not_applicable"
    treatmentContext: Literal[
        "treatment_naive",
        "post_platinum_chemotherapy",
        "post_egfr_tki",
        "post_chemo_immunotherapy",
        "post_chemoradiation",
        "post_surgery",
        "unspecified",
    ] = "unspecified"
    clinicalModifiers: ClinicalModifiersModel = Field(default_factory=ClinicalModifiersModel)


class CitationRefModel(BaseModel):
    sourceId: str
    title: str
    summary: str | None = None
    year: int | None = None


class SemanticEvidenceItemModel(BaseModel):
    chunkId: str
    sourceType: Literal["pubmed", "esmo"]
    sourceId: str
    title: str
    snippet: str
    score: float
    denseScore: float
    sparseScore: float
    mappedTopicId: str | None = None
    mappedTopicTitle: str | None = None


class SemanticGuidelineCandidateModel(BaseModel):
    topicId: str
    topicTitle: str
    score: float
    supportingChunkIds: list[str] = Field(default_factory=list)


class ExplainabilitySummaryModel(BaseModel):
    summary: str
    grounded: bool
    sourceChunkIds: list[str] = Field(default_factory=list)
    providerStatus: str = "grounded_local"
    provider: str | None = None
    model: str | None = None
    promptVersion: str = "local-summary-v1"
    latencyMs: int | None = None
    validationStatus: str = "not_applicable"
    sourceIds: list[str] = Field(default_factory=list)


class EvidenceExplainabilityStudySummaryModel(BaseModel):
    objective: str
    signal: str
    takeaway: str


class EvidenceExplainabilitySourceAnchorModel(BaseModel):
    sourceId: str
    title: str
    snippet: str
    year: int | None = None


class EvidenceExplainabilityModel(BaseModel):
    evidenceId: str
    scoreRationale: str
    studySummary: EvidenceExplainabilityStudySummaryModel
    sourceAnchors: list[EvidenceExplainabilitySourceAnchorModel] = Field(default_factory=list)
    grounded: bool
    providerStatus: str = "grounded_local"
    provider: str | None = None
    model: str | None = None
    promptVersion: str = "local-summary-v1"
    latencyMs: int | None = None
    validationStatus: str = "not_applicable"
    sourceIds: list[str] = Field(default_factory=list)


class UncertaintyFlagsExplainabilityModel(BaseModel):
    summary: str
    whyFlagsExist: str
    whatItMeans: str
    flags: list[str] = Field(default_factory=list)
    grounded: bool = True
    providerStatus: str = "grounded_local"
    provider: str | None = None
    model: str | None = None
    promptVersion: str = "local-uncertainty-flags-v1"
    latencyMs: int | None = None
    validationStatus: str = "not_applicable"


class ScoreBreakdownModel(BaseModel):
    evidenceStrength: int
    datasetRobustness: int
    sourceCredibility: int
    recency: int


class TopEvidenceItemModel(BaseModel):
    rank: int
    evidenceId: str
    title: str
    abstract: str | None = None
    journalTitle: str | None = None
    publicationYear: int | None = None
    ersTotal: int
    ersBreakdown: ScoreBreakdownModel
    mappedTopicId: str | None = None
    mappedTopicTitle: str | None = None
    mappingLabel: Literal["aligned", "guideline_silent", "conflict"]
    applicabilityNote: str
    citations: list[CitationRefModel]


class ManualReviewEvidenceItemModel(BaseModel):
    evidenceId: str
    title: str
    abstract: str | None = None
    journalTitle: str | None = None
    publicationYear: int | None = None
    classificationStatus: Literal["scored", "manual_review_required"]
    manualReviewReason: Literal["evidence_type_unspecified"]
    mappedTopicId: str | None = None
    mappedTopicTitle: str | None = None
    mappingLabel: Literal["aligned", "guideline_silent", "conflict"]
    potentialConflict: bool = False
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
    engine: Literal["deterministic", "semantic_retrieval_lab"] = "deterministic"
    retrievalMode: Literal["hybrid", "dense_only"] = "hybrid"
    vectorStore: str = "deterministic_only"
    embeddingModel: str = "none"
    chunkingStrategyVersion: str = "none"
    topEvidence: list[TopEvidenceItemModel]
    manualReviewEvidence: list[ManualReviewEvidenceItemModel] = Field(default_factory=list)
    secondaryReferences: list[SecondaryReferenceModel]
    uncertaintyFlags: list[str]
    safetyFooterKey: str
    traceId: str
    retrievalCandidateCount: int = 0
    semanticEvidence: list[SemanticEvidenceItemModel] = Field(default_factory=list)
    semanticGuidelineCandidates: list[SemanticGuidelineCandidateModel] = Field(default_factory=list)
    explainabilitySummary: ExplainabilitySummaryModel | None = None
    semanticCandidateOnlyCount: int = 0


class TracePayloadModel(BaseModel):
    traceId: str
    runId: str
    inputSchemaVersion: str
    rulesetVersion: str
    corpusVersion: str
    engine: Literal["deterministic", "semantic_retrieval_lab"] = "deterministic"
    retrievalMode: Literal["hybrid", "dense_only"] = "hybrid"
    vectorStore: str = "deterministic_only"
    embeddingModel: str = "none"
    chunkingStrategyVersion: str = "none"
    gateCandidateCount: int
    eligibleCount: int
    topEvidenceCount: int
    manualReviewCount: int = 0
    secondaryCount: int
    uncertaintyFlags: list[str]
    safetyFooterKey: str
    retrievalCandidateCount: int = 0
    semanticCandidateOnlyCount: int = 0


class GovernancePolicyModel(BaseModel):
    scope: str
    frozenLabelVocabulary: list[str]
    hardStops: list[str]
    softReviewTriggers: list[str]
    safetyBoundaries: list[str]


class AppVersionModel(BaseModel):
    productVersion: str
    uiVersion: str
    backendVersion: str
    rulesetVersion: str
    corpusVersion: str
    releaseDate: str | None = None
    buildLabel: str
    notes: list[str] = Field(default_factory=list)


class ImportRequestModel(BaseModel):
    path: str | None = None
    mode: Literal["replace", "append"] = "replace"


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


class DatasetBrowserEntryModel(BaseModel):
    path: str
    kind: Literal["folder", "file"]
    fileCount: int


class DatasetBrowserResponseModel(BaseModel):
    datasetKind: Literal["esmo", "pubmed"]
    rootPath: str
    entries: list[DatasetBrowserEntryModel]


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
    semanticDocuments: int = 0
    semanticChunks: int = 0
    semanticCollections: dict[str, int] = Field(default_factory=dict)


class ImportDebugConfigModel(BaseModel):
    strictMvpPubmed: bool = False
    runtimeEngine: Literal["deterministic", "semantic_retrieval_lab"] = "deterministic"
    semanticRetrievalEnabled: bool = False
    retrievalMode: Literal["hybrid", "dense_only"] = "hybrid"
    llmImportAssistEnabled: bool = False
    llmExplainabilityEnabled: bool = False


class ImportDebugLogEntryModel(BaseModel):
    timestamp: datetime
    level: str
    event: str
    datasetKind: str | None = None
    path: str | None = None
    message: str
    details: dict[str, str | int | bool | float | None] | dict[str, object] = Field(default_factory=dict)


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


class EngineBenchmarkCaseMetricsModel(BaseModel):
    engine: Literal["deterministic", "semantic_retrieval_lab"]
    retrievalMode: Literal["hybrid", "dense_only"]
    topEvidenceCount: int
    alignedCount: int
    guidelineSilentCount: int
    conflictCount: int
    manualReviewCount: int
    secondaryCount: int
    uncertaintyFlagCount: int
    retrievalCandidateCount: int = 0
    semanticCandidateOnlyCount: int = 0
    topTopicTitles: list[str] = Field(default_factory=list)
    expectedRecall: float | None = None
    expectedLabelAccuracy: float | None = None
    observedPrimaryLabel: Literal["aligned", "guideline_silent", "conflict"] | None = None
    observedPrimaryTopicId: str | None = None
    observedPrimaryTopicTitle: str | None = None


class EngineBenchmarkCaseReferenceModel(BaseModel):
    expectedPrimaryLabel: Literal["aligned", "guideline_silent", "conflict"] | None = None
    expectedGuidelineTopicId: str | None = None
    expectedGuidelineTopicTitle: str | None = None
    expectedEvidenceIds: list[str] = Field(default_factory=list)
    expectedLabelByEvidenceId: dict[str, Literal["aligned", "guideline_silent", "conflict"]] = Field(default_factory=dict)


class EngineBenchmarkCaseComparisonModel(BaseModel):
    observedPrimaryLabel: Literal["aligned", "guideline_silent", "conflict"] | None = None
    observedGuidelineTopicId: str | None = None
    observedGuidelineTopicTitle: str | None = None
    matchedExpectedEvidenceIds: list[str] = Field(default_factory=list)
    missedExpectedEvidenceIds: list[str] = Field(default_factory=list)
    unexpectedPromotedEvidenceIds: list[str] = Field(default_factory=list)
    topicMatch: bool | None = None
    primaryLabelHit: bool | None = None
    why: str = ""
    sourceFingerprint: str
    runtimeConfigFingerprint: str


class EngineBenchmarkCaseResultModel(BaseModel):
    caseId: str
    caseLabel: str
    detail: str
    category: str | None = None
    clinicalQuestion: str | None = None
    status: Literal["completed", "failed"]
    error: str | None = None
    metrics: EngineBenchmarkCaseMetricsModel | None = None
    reference: EngineBenchmarkCaseReferenceModel | None = None
    comparison: EngineBenchmarkCaseComparisonModel | None = None


class EngineBenchmarkAggregateModel(BaseModel):
    caseCount: int
    casesWithAlignedEvidence: int
    totalTopEvidence: int
    totalAligned: int
    totalGuidelineSilent: int
    totalConflict: int
    totalManualReview: int
    totalSecondary: int
    totalUncertaintyFlags: int
    totalRetrievalCandidates: int
    totalRetrievalCaseHits: int = 0
    retrievalOverlapCount: int = 0
    retrievalMultiCaseEvidenceCount: int = 0
    retrievalOverlapRate: float = 0.0
    totalSemanticCandidateOnly: int
    averageTopEvidence: float
    averageAligned: float
    averageUncertaintyFlags: float
    averageExpectedRecall: float | None = None
    averageExpectedLabelAccuracy: float | None = None
    topicMatchRate: float | None = None
    primaryLabelHitRate: float | None = None
    expectedLabelDistribution: dict[str, int] = Field(default_factory=dict)
    observedLabelDistribution: dict[str, int] = Field(default_factory=dict)
    packCompleteness: str
    quantitativeGoldensComplete: bool


class EngineBenchmarkCaseDeltaModel(BaseModel):
    caseId: str
    caseLabel: str
    retrievalDelta: int = 0
    alignedDelta: int = 0
    guidelineSilentDelta: int = 0
    manualReviewDelta: int = 0
    hybridRetrievalCount: int = 0
    hybridOnlyRetrievalCount: int = 0
    promotedAlignedCount: int = 0
    promotedGuidelineSilentCount: int = 0
    promotedManualReviewCount: int = 0
    sampleRetrievalEvidenceIds: list[str] = Field(default_factory=list)
    sampleHybridOnlyRetrievalEvidenceIds: list[str] = Field(default_factory=list)
    samplePromotedAlignedEvidenceIds: list[str] = Field(default_factory=list)
    samplePromotedGuidelineSilentEvidenceIds: list[str] = Field(default_factory=list)
    samplePromotedManualReviewEvidenceIds: list[str] = Field(default_factory=list)


class EngineBenchmarkRetrievalBreakdownModel(BaseModel):
    delta: int = 0
    deterministicUniqueEvidenceCount: int = 0
    hybridUniqueEvidenceCount: int = 0
    hybridCaseHitCountTotal: int = 0
    hybridOverlapCount: int = 0
    hybridMultiCaseEvidenceCount: int = 0
    hybridOverlapRate: float = 0.0
    hybridOnlyEvidenceCount: int = 0
    sampleHybridOnlyEvidenceIds: list[str] = Field(default_factory=list)
    sampleMultiCaseEvidenceIds: list[str] = Field(default_factory=list)


class EngineBenchmarkDecisionLayerBreakdownModel(BaseModel):
    alignedDelta: int = 0
    guidelineSilentDelta: int = 0
    manualReviewDelta: int = 0
    promotedAlignedUniqueCount: int = 0
    promotedGuidelineSilentUniqueCount: int = 0
    promotedManualReviewUniqueCount: int = 0
    samplePromotedAlignedEvidenceIds: list[str] = Field(default_factory=list)
    samplePromotedGuidelineSilentEvidenceIds: list[str] = Field(default_factory=list)
    samplePromotedManualReviewEvidenceIds: list[str] = Field(default_factory=list)


class EngineBenchmarkExplainabilityModel(BaseModel):
    retrieval: EngineBenchmarkRetrievalBreakdownModel
    decisionLayer: EngineBenchmarkDecisionLayerBreakdownModel
    caseDeltas: list[EngineBenchmarkCaseDeltaModel] = Field(default_factory=list)


class EngineBenchmarkEngineResultModel(BaseModel):
    engineKey: Literal["deterministic", "hybrid_semantic"]
    label: str
    runtimeEngine: Literal["deterministic", "semantic_retrieval_lab"]
    retrievalMode: Literal["hybrid", "dense_only"]
    status: Literal["available", "unavailable"]
    aggregate: EngineBenchmarkAggregateModel
    cases: list[EngineBenchmarkCaseResultModel]
    notes: list[str] = Field(default_factory=list)


class EngineBenchmarkSummaryModel(BaseModel):
    packLabel: str
    semanticChangesDecisionLayer: bool
    headline: str
    recommendedTakeaway: str
    benchmarkNarrative: ExplainabilitySummaryModel | None = None


class EngineBenchmarkRequestModel(BaseModel):
    packId: Literal["demo_presets", "frozen_pack"] = "demo_presets"
    retrievalMode: Literal["hybrid", "dense_only"] = "hybrid"
    forceRefresh: bool = False


class EngineBenchmarkMetaModel(BaseModel):
    cached: bool = False
    cacheKey: str
    benchmarkVersion: str
    pubmedBatchId: str | None = None
    esmoBatchId: str | None = None
    pubmedSemanticJobId: str | None = None
    esmoSemanticJobId: str | None = None
    sourceFingerprint: str
    runtimeConfigFingerprint: str
    vectorStore: str | None = None
    embeddingModel: str | None = None


class EngineBenchmarkResultModel(BaseModel):
    evalRunId: str
    packId: str
    summary: EngineBenchmarkSummaryModel
    engines: list[EngineBenchmarkEngineResultModel]
    breakdown: EngineBenchmarkExplainabilityModel
    meta: EngineBenchmarkMetaModel
    notes: list[str] = Field(default_factory=list)


class SemanticImportStatusModel(BaseModel):
    datasetKind: Literal["pubmed", "esmo"]
    latestBatchId: str | None = None
    latestStatus: str | None = None
    documentCount: int = 0
    chunkCount: int = 0
    latestJob: dict[str, object] | None = None


class EmbeddingManifestModel(BaseModel):
    pointCount: int
    sourceCounts: dict[str, int]
    histologyCounts: dict[str, int]
    embeddingModel: str
    projectionMethod: str
    vectorStore: str


class EmbeddingPointModel(BaseModel):
    pointId: str
    chunkId: str
    sourceType: Literal["pubmed", "esmo"]
    sourceId: str
    title: str
    topicId: str | None = None
    histology: str
    x: float
    y: float
    label: str


class EmbeddingNeighborModel(BaseModel):
    pointId: str
    title: str
    sourceType: Literal["pubmed", "esmo"]
    sourceId: str
    similarity: float
