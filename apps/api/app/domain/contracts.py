from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal


BiomarkerFlag = Literal["yes", "no", "unspecified"]
PDL1Bucket = Literal["lt1", "1to49", "ge50", "unspecified"]
DiseaseSetting = Literal["early", "locally_advanced", "metastatic", "mixed"]
Histology = Literal["adenocarcinoma", "squamous", "non_squamous", "mixed", "all_nsclc"]
LineOfTherapy = Literal["first_line", "second_line", "later_line", "mixed", "unspecified"]
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
class VignetteInput:
    cancerType: Literal["NSCLC"]
    diseaseSetting: Literal["early", "locally_advanced", "metastatic"]
    histology: Literal["adenocarcinoma", "squamous", "non_squamous"]
    performanceStatus: PerformanceStatus
    biomarkers: Biomarkers
    lineOfTherapy: LineOfTherapy = "unspecified"


@dataclass(slots=True)
class PopulationTags:
    disease: Literal["NSCLC"]
    diseaseSetting: DiseaseSetting
    histology: Histology
    biomarkers: dict[str, str]
    lineOfTherapy: LineOfTherapy = "unspecified"


@dataclass(slots=True)
class EvidenceRecord:
    evidenceId: str
    title: str
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


@dataclass(slots=True)
class TopEvidenceItem:
    rank: int
    evidenceId: str
    title: str
    publicationYear: int | None
    ersTotal: int
    ersBreakdown: ScoreBreakdown
    mappedTopicId: str | None
    mappedTopicTitle: str | None
    mappingLabel: MappingLabel
    applicabilityNote: str
    citations: list[CitationRef]


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
    topEvidence: list[TopEvidenceItem]
    secondaryReferences: list[SecondaryReference]
    uncertaintyFlags: list[str]
    safetyFooterKey: str
    traceId: str
