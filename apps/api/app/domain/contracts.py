from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal


BiomarkerFlag = Literal["yes", "no", "unspecified"]
PDL1Bucket = Literal["lt1", "1to49", "ge50", "any", "unspecified"]
DiseaseSetting = Literal["early", "locally_advanced", "metastatic", "mixed"]
Histology = Literal["adenocarcinoma", "squamous", "non_squamous", "mixed", "all_nsclc"]
DiseaseStage = Literal["stage_i", "stage_ii", "stage_iii", "stage_iv", "unspecified"]
ResectabilityStatus = Literal["resected", "unresectable", "not_applicable", "unspecified"]
TreatmentContext = Literal[
    "treatment_naive",
    "post_platinum_chemotherapy",
    "post_egfr_tki",
    "post_chemo_immunotherapy",
    "post_chemoradiation",
    "post_surgery",
    "unspecified",
]
LineOfTherapy = Literal["first_line", "second_line", "later_line", "adjuvant", "consolidation", "mixed", "unspecified"]
PerformanceStatus = Literal["0", "1", "2", "3", "4"]
EvidenceType = Literal[
    "guideline",
    "systematic_review",
    "phase3_rct",
    "phase2_rct",
    "prospective_obs",
    "retrospective",
    "case_series",
    "expert_opinion",
    "unspecified",
]
SourceCategory = Literal[
    "guideline_body",
    "high_impact_journal",
    "specialty_journal",
    "preprint",
    "industry_whitepaper",
]
GuidelineStance = Literal["recommend", "conditional", "do_not_recommend", "not_covered"]
MappingLabel = Literal["aligned", "guideline_silent", "conflict"]
EvidenceClassificationStatus = Literal["scored", "manual_review_required"]
ManualReviewReason = Literal["evidence_type_unspecified"]
RuntimeEngine = Literal["deterministic", "semantic_retrieval_lab"]
RetrievalMode = Literal["hybrid", "dense_only"]


@dataclass(slots=True)
class Biomarkers:
    EGFR: BiomarkerFlag
    ALK: BiomarkerFlag
    ROS1: BiomarkerFlag
    PDL1Bucket: PDL1Bucket = "unspecified"
    BRAF: BiomarkerFlag = "unspecified"
    RET: BiomarkerFlag = "unspecified"
    MET: BiomarkerFlag = "unspecified"
    KRAS: BiomarkerFlag = "unspecified"
    NTRK: BiomarkerFlag = "unspecified"
    HER2: BiomarkerFlag = "unspecified"
    EGFRExon20ins: BiomarkerFlag = "unspecified"


@dataclass(slots=True)
class ClinicalModifiers:
    brainMetastases: BiomarkerFlag = "unspecified"


@dataclass(slots=True)
class VignetteInput:
    cancerType: Literal["NSCLC"]
    diseaseSetting: Literal["early", "locally_advanced", "metastatic"]
    histology: Literal["adenocarcinoma", "squamous", "non_squamous"]
    performanceStatus: PerformanceStatus
    biomarkers: Biomarkers
    lineOfTherapy: LineOfTherapy = "unspecified"
    diseaseStage: DiseaseStage = "unspecified"
    resectabilityStatus: ResectabilityStatus = "not_applicable"
    treatmentContext: TreatmentContext = "unspecified"
    clinicalModifiers: ClinicalModifiers = field(default_factory=ClinicalModifiers)


@dataclass(slots=True)
class PopulationTags:
    disease: Literal["NSCLC"]
    diseaseSetting: DiseaseSetting
    histology: Histology
    biomarkers: dict[str, str]
    lineOfTherapy: LineOfTherapy = "unspecified"
    diseaseStage: DiseaseStage = "unspecified"
    resectabilityStatus: ResectabilityStatus = "unspecified"
    treatmentContext: TreatmentContext = "unspecified"
    brainMetastases: BiomarkerFlag = "unspecified"


@dataclass(slots=True)
class EvidenceRecord:
    evidenceId: str
    title: str
    abstract: str | None
    journalTitle: str | None
    publicationYear: int | None
    evidenceType: EvidenceType
    relevantN: int | None
    sourceCategory: SourceCategory | None
    populationTags: PopulationTags
    interventionTags: list[str]
    outcomeTags: list[str]


@dataclass(slots=True)
class TopicApplicability:
    diseaseSetting: list[Literal["early", "locally_advanced", "metastatic"]]
    histology: list[Literal["adenocarcinoma", "squamous", "non_squamous"]]
    biomarkerConditions: list[str]
    lineOfTherapy: list[LineOfTherapy] = field(default_factory=lambda: ["unspecified"])
    diseaseStage: list[DiseaseStage] = field(default_factory=lambda: ["unspecified"])
    resectabilityStatus: list[ResectabilityStatus] = field(default_factory=lambda: ["unspecified"])
    treatmentContext: list[TreatmentContext] = field(default_factory=lambda: ["unspecified"])


@dataclass(slots=True)
class GuidelineTopic:
    topicId: str
    topicTitle: str
    topicApplicability: TopicApplicability
    topicInterventionTags: list[str]
    guidelineStance: GuidelineStance
    stanceNotes: str | None = None
    prerequisites: list[str] = field(default_factory=list)


@dataclass(slots=True)
class ScoreBreakdown:
    evidenceStrength: int
    datasetRobustness: int
    sourceCredibility: int
    recency: int

    @property
    def total(self) -> int:
        return self.evidenceStrength + self.datasetRobustness + self.sourceCredibility + self.recency


@dataclass(slots=True)
class CitationRef:
    sourceId: str
    title: str
    year: int | None
    summary: str | None = None


@dataclass(slots=True)
class SemanticEvidenceItem:
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


@dataclass(slots=True)
class SemanticGuidelineCandidate:
    topicId: str
    topicTitle: str
    score: float
    supportingChunkIds: list[str] = field(default_factory=list)


@dataclass(slots=True)
class ExplainabilitySummary:
    summary: str
    grounded: bool
    sourceChunkIds: list[str] = field(default_factory=list)
    providerStatus: str = "grounded_local"
    provider: str | None = None
    model: str | None = None
    promptVersion: str = "local-summary-v1"
    latencyMs: int | None = None
    validationStatus: str = "not_applicable"
    sourceIds: list[str] = field(default_factory=list)


@dataclass(slots=True)
class EvidenceExplainabilityStudySummary:
    objective: str
    signal: str
    takeaway: str


@dataclass(slots=True)
class EvidenceExplainabilitySourceAnchor:
    sourceId: str
    title: str
    snippet: str
    year: int | None = None


@dataclass(slots=True)
class EvidenceExplainability:
    evidenceId: str
    scoreRationale: str
    studySummary: EvidenceExplainabilityStudySummary
    sourceAnchors: list[EvidenceExplainabilitySourceAnchor] = field(default_factory=list)
    grounded: bool = True
    providerStatus: str = "grounded_local"
    provider: str | None = None
    model: str | None = None
    promptVersion: str = "local-summary-v1"
    latencyMs: int | None = None
    validationStatus: str = "not_applicable"
    sourceIds: list[str] = field(default_factory=list)


@dataclass(slots=True)
class UncertaintyFlagsExplainability:
    summary: str
    whyFlagsExist: str
    whatItMeans: str
    flags: list[str] = field(default_factory=list)
    grounded: bool = True
    providerStatus: str = "grounded_local"
    provider: str | None = None
    model: str | None = None
    promptVersion: str = "local-uncertainty-flags-v1"
    latencyMs: int | None = None
    validationStatus: str = "not_applicable"


@dataclass(slots=True)
class TopEvidenceItem:
    rank: int
    evidenceId: str
    title: str
    abstract: str | None
    journalTitle: str | None
    publicationYear: int | None
    ersTotal: int
    ersBreakdown: ScoreBreakdown
    mappedTopicId: str | None
    mappedTopicTitle: str | None
    mappingLabel: MappingLabel
    applicabilityNote: str
    citations: list[CitationRef]


@dataclass(slots=True)
class ManualReviewEvidenceItem:
    evidenceId: str
    title: str
    abstract: str | None
    journalTitle: str | None
    publicationYear: int | None
    classificationStatus: EvidenceClassificationStatus
    manualReviewReason: ManualReviewReason
    mappedTopicId: str | None
    mappedTopicTitle: str | None
    mappingLabel: MappingLabel
    applicabilityNote: str
    citations: list[CitationRef]
    potentialConflict: bool = False


@dataclass(slots=True)
class SecondaryReference:
    evidenceId: str
    exclusionReasons: list[str]


@dataclass(slots=True)
class RunInfo:
    id: str
    status: Literal["queued", "running", "completed", "failed"]
    rulesetVersion: str
    corpusVersion: str
    createdAt: datetime
    latencyMs: int | None = None


@dataclass(slots=True)
class AnalyzeRunResponse:
    run: RunInfo
    engine: RuntimeEngine
    retrievalMode: RetrievalMode
    vectorStore: str
    embeddingModel: str
    chunkingStrategyVersion: str
    topEvidence: list[TopEvidenceItem]
    manualReviewEvidence: list[ManualReviewEvidenceItem]
    secondaryReferences: list[SecondaryReference]
    uncertaintyFlags: list[str]
    safetyFooterKey: str
    traceId: str
    retrievalCandidateCount: int = 0
    semanticEvidence: list[SemanticEvidenceItem] = field(default_factory=list)
    semanticGuidelineCandidates: list[SemanticGuidelineCandidate] = field(default_factory=list)
    explainabilitySummary: ExplainabilitySummary | None = None
    semanticCandidateOnlyCount: int = 0
