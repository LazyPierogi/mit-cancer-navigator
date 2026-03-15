export type VignetteInput = {
  cancerType: "NSCLC";
  diseaseSetting: "early" | "locally_advanced" | "metastatic";
  histology: "adenocarcinoma" | "squamous" | "non_squamous";
  lineOfTherapy: "first_line" | "second_line" | "later_line" | "adjuvant" | "consolidation" | "mixed" | "unspecified";
  performanceStatus: "0" | "1" | "2" | "3" | "4";
  diseaseStage: "stage_i" | "stage_ii" | "stage_iii" | "stage_iv" | "unspecified";
  resectabilityStatus: "resected" | "unresectable" | "not_applicable" | "unspecified";
  treatmentContext:
    | "treatment_naive"
    | "post_platinum_chemotherapy"
    | "post_egfr_tki"
    | "post_chemo_immunotherapy"
    | "post_chemoradiation"
    | "post_surgery"
    | "unspecified";
  biomarkers: {
    EGFR: "yes" | "no" | "unspecified";
    ALK: "yes" | "no" | "unspecified";
    ROS1: "yes" | "no" | "unspecified";
    PDL1Bucket: "lt1" | "1to49" | "ge50" | "unspecified";
    BRAF: "yes" | "no" | "unspecified";
    RET: "yes" | "no" | "unspecified";
    MET: "yes" | "no" | "unspecified";
    KRAS: "yes" | "no" | "unspecified";
    NTRK: "yes" | "no" | "unspecified";
    HER2: "yes" | "no" | "unspecified";
    EGFRExon20ins: "yes" | "no" | "unspecified";
  };
  clinicalModifiers: {
    brainMetastases: "yes" | "no" | "unspecified";
  };
};

export type AnalyzeRunResponse = {
  run: {
    id: string;
    status: "queued" | "running" | "completed" | "failed";
    rulesetVersion: string;
    corpusVersion: string;
    createdAt: string;
    latencyMs?: number;
  };
  engine: "deterministic" | "semantic_retrieval_lab";
  retrievalMode: "hybrid" | "dense_only";
  vectorStore: string;
  embeddingModel: string;
  chunkingStrategyVersion: string;
  topEvidence: Array<{
    rank: number;
    evidenceId: string;
    title: string;
    abstract?: string | null;
    journalTitle?: string | null;
    publicationYear: number | null;
    ersTotal: number;
    ersBreakdown: {
      evidenceStrength: number;
      datasetRobustness: number;
      sourceCredibility: number;
      recency: number;
    };
    mappedTopicId: string | null;
    mappedTopicTitle: string | null;
    mappingLabel: "aligned" | "guideline_silent" | "conflict";
    applicabilityNote: string;
    citations: Array<{
      sourceId: string;
      title: string;
      summary?: string | null;
      year: number | null;
    }>;
  }>;
  manualReviewEvidence: Array<{
    evidenceId: string;
    title: string;
    abstract?: string | null;
    journalTitle?: string | null;
    publicationYear: number | null;
    classificationStatus: "scored" | "manual_review_required";
    manualReviewReason: "evidence_type_unspecified";
    mappedTopicId: string | null;
    mappedTopicTitle: string | null;
    mappingLabel: "aligned" | "guideline_silent" | "conflict";
    potentialConflict: boolean;
    applicabilityNote: string;
    citations: Array<{
      sourceId: string;
      title: string;
      summary?: string | null;
      year: number | null;
    }>;
  }>;
  secondaryReferences: Array<{
    evidenceId: string;
    exclusionReasons: string[];
  }>;
  uncertaintyFlags: string[];
  safetyFooterKey: string;
  traceId: string;
  retrievalCandidateCount: number;
  semanticEvidence: Array<{
    chunkId: string;
    sourceType: "pubmed" | "esmo";
    sourceId: string;
    title: string;
    snippet: string;
    score: number;
    denseScore: number;
    sparseScore: number;
    mappedTopicId: string | null;
    mappedTopicTitle: string | null;
  }>;
  semanticGuidelineCandidates: Array<{
    topicId: string;
    topicTitle: string;
    score: number;
    supportingChunkIds: string[];
  }>;
  explainabilitySummary: {
    summary: string;
    grounded: boolean;
    sourceChunkIds: string[];
    providerStatus: string;
    provider: string | null;
    model: string | null;
    promptVersion: string;
    latencyMs: number | null;
    validationStatus: string;
    sourceIds: string[];
  } | null;
  semanticCandidateOnlyCount: number;
};

export type EvidenceExplainability = {
  evidenceId: string;
  scoreRationale: string;
  studySummary: {
    objective: string;
    signal: string;
    takeaway: string;
  };
  sourceAnchors: Array<{
    sourceId: string;
    title: string;
    snippet: string;
    year: number | null;
  }>;
  grounded: boolean;
  providerStatus: string;
  provider: string | null;
  model: string | null;
  promptVersion: string;
  latencyMs: number | null;
  validationStatus: string;
  sourceIds: string[];
};

export type UncertaintyFlagsExplainability = {
  summary: string;
  whyFlagsExist: string;
  whatItMeans: string;
  flags: string[];
  grounded: boolean;
  providerStatus: string;
  provider: string | null;
  model: string | null;
  promptVersion: string;
  latencyMs: number | null;
  validationStatus: string;
};

export type TracePayload = {
  traceId: string;
  runId: string;
  inputSchemaVersion: string;
  rulesetVersion: string;
  corpusVersion: string;
  engine: "deterministic" | "semantic_retrieval_lab";
  retrievalMode: "hybrid" | "dense_only";
  vectorStore: string;
  embeddingModel: string;
  chunkingStrategyVersion: string;
  gateCandidateCount: number;
  eligibleCount: number;
  topEvidenceCount: number;
  manualReviewCount: number;
  secondaryCount: number;
  uncertaintyFlags: string[];
  safetyFooterKey: string;
  retrievalCandidateCount: number;
  semanticCandidateOnlyCount: number;
};

export type EngineBenchmarkRequest = {
  packId: "demo_presets" | "frozen_pack";
  retrievalMode: "hybrid" | "dense_only";
  forceRefresh?: boolean;
};

export type EngineBenchmarkCaseMetrics = {
  engine: "deterministic" | "semantic_retrieval_lab";
  retrievalMode: "hybrid" | "dense_only";
  topEvidenceCount: number;
  alignedCount: number;
  guidelineSilentCount: number;
  conflictCount: number;
  manualReviewCount: number;
  secondaryCount: number;
  uncertaintyFlagCount: number;
  retrievalCandidateCount: number;
  semanticCandidateOnlyCount: number;
  topTopicTitles: string[];
  expectedRecall: number | null;
  expectedLabelAccuracy: number | null;
  observedPrimaryLabel: "aligned" | "guideline_silent" | "conflict" | null;
  observedPrimaryTopicId: string | null;
  observedPrimaryTopicTitle: string | null;
};

export type EngineBenchmarkCaseReference = {
  expectedPrimaryLabel: "aligned" | "guideline_silent" | "conflict" | null;
  expectedGuidelineTopicId: string | null;
  expectedGuidelineTopicTitle: string | null;
  expectedEvidenceIds: string[];
  expectedLabelByEvidenceId: Record<string, "aligned" | "guideline_silent" | "conflict">;
};

export type EngineBenchmarkCaseComparison = {
  observedPrimaryLabel: "aligned" | "guideline_silent" | "conflict" | null;
  observedGuidelineTopicId: string | null;
  observedGuidelineTopicTitle: string | null;
  matchedExpectedEvidenceIds: string[];
  missedExpectedEvidenceIds: string[];
  unexpectedPromotedEvidenceIds: string[];
  topicMatch: boolean | null;
  primaryLabelHit: boolean | null;
  why: string;
  sourceFingerprint: string;
  runtimeConfigFingerprint: string;
};

export type EngineBenchmarkCaseResult = {
  caseId: string;
  caseLabel: string;
  detail: string;
  category: string | null;
  clinicalQuestion: string | null;
  status: "completed" | "failed";
  error: string | null;
  metrics: EngineBenchmarkCaseMetrics | null;
  reference: EngineBenchmarkCaseReference | null;
  comparison: EngineBenchmarkCaseComparison | null;
};

export type EngineBenchmarkAggregate = {
  caseCount: number;
  casesWithAlignedEvidence: number;
  totalTopEvidence: number;
  totalAligned: number;
  totalGuidelineSilent: number;
  totalConflict: number;
  totalManualReview: number;
  totalSecondary: number;
  totalUncertaintyFlags: number;
  totalRetrievalCandidates: number;
  totalRetrievalCaseHits: number;
  retrievalOverlapCount: number;
  retrievalMultiCaseEvidenceCount: number;
  retrievalOverlapRate: number;
  totalSemanticCandidateOnly: number;
  averageTopEvidence: number;
  averageAligned: number;
  averageUncertaintyFlags: number;
  averageExpectedRecall: number | null;
  averageExpectedLabelAccuracy: number | null;
  topicMatchRate: number | null;
  primaryLabelHitRate: number | null;
  expectedLabelDistribution: Record<string, number>;
  observedLabelDistribution: Record<string, number>;
  packCompleteness: string;
  quantitativeGoldensComplete: boolean;
};

export type EngineBenchmarkCaseDelta = {
  caseId: string;
  caseLabel: string;
  retrievalDelta: number;
  alignedDelta: number;
  guidelineSilentDelta: number;
  manualReviewDelta: number;
  hybridRetrievalCount: number;
  hybridOnlyRetrievalCount: number;
  promotedAlignedCount: number;
  promotedGuidelineSilentCount: number;
  promotedManualReviewCount: number;
  sampleRetrievalEvidenceIds: string[];
  sampleHybridOnlyRetrievalEvidenceIds: string[];
  samplePromotedAlignedEvidenceIds: string[];
  samplePromotedGuidelineSilentEvidenceIds: string[];
  samplePromotedManualReviewEvidenceIds: string[];
};

export type EngineBenchmarkBreakdown = {
  retrieval: {
    delta: number;
    deterministicUniqueEvidenceCount: number;
    hybridUniqueEvidenceCount: number;
    hybridCaseHitCountTotal: number;
    hybridOverlapCount: number;
    hybridMultiCaseEvidenceCount: number;
    hybridOverlapRate: number;
    hybridOnlyEvidenceCount: number;
    sampleHybridOnlyEvidenceIds: string[];
    sampleMultiCaseEvidenceIds: string[];
  };
  decisionLayer: {
    alignedDelta: number;
    guidelineSilentDelta: number;
    manualReviewDelta: number;
    promotedAlignedUniqueCount: number;
    promotedGuidelineSilentUniqueCount: number;
    promotedManualReviewUniqueCount: number;
    samplePromotedAlignedEvidenceIds: string[];
    samplePromotedGuidelineSilentEvidenceIds: string[];
    samplePromotedManualReviewEvidenceIds: string[];
  };
  caseDeltas: EngineBenchmarkCaseDelta[];
};

export type EngineBenchmarkEngineResult = {
  engineKey: "deterministic" | "hybrid_semantic";
  label: string;
  runtimeEngine: "deterministic" | "semantic_retrieval_lab";
  retrievalMode: "hybrid" | "dense_only";
  status: "available" | "unavailable";
  aggregate: EngineBenchmarkAggregate;
  cases: EngineBenchmarkCaseResult[];
  notes: string[];
};

export type EngineBenchmarkSummary = {
  packLabel: string;
  semanticChangesDecisionLayer: boolean;
  headline: string;
  recommendedTakeaway: string;
  benchmarkNarrative: AnalyzeRunResponse["explainabilitySummary"] | null;
};

export type EngineBenchmarkMeta = {
  cached: boolean;
  cacheKey: string;
  benchmarkVersion: string;
  pubmedBatchId: string | null;
  esmoBatchId: string | null;
  pubmedSemanticJobId: string | null;
  esmoSemanticJobId: string | null;
  sourceFingerprint: string;
  runtimeConfigFingerprint: string;
  vectorStore: string | null;
  embeddingModel: string | null;
};

export type EngineBenchmarkResult = {
  evalRunId: string;
  packId: string;
  summary: EngineBenchmarkSummary;
  engines: EngineBenchmarkEngineResult[];
  breakdown: EngineBenchmarkBreakdown;
  meta: EngineBenchmarkMeta;
  notes: string[];
};

export type ValidationIssue = {
  severity: string;
  code: string;
  message: string;
  record_id?: string | null;
};

export type ValidationReport = {
  datasetKind: string;
  datasetShape: string;
  path: string;
  errorCount: number;
  warningCount: number;
  info: string[];
  errors: ValidationIssue[];
  warnings: ValidationIssue[];
};

export type DatasetBrowserEntry = {
  path: string;
  kind: "folder" | "file";
  fileCount: number;
};

export type DatasetBrowserResponse = {
  datasetKind: "esmo" | "pubmed";
  rootPath: string;
  entries: DatasetBrowserEntry[];
};

export type ImportBatch = {
  batchId: string;
  datasetKind: string;
  datasetShape: string;
  sourcePath: string;
  status: string;
  recordCount: number;
  importedCount: number;
  errorCount: number;
  warningCount: number;
  validation: ValidationReport;
  notes: string[];
  createdAt: string;
};

export type ImportSummaryKind = {
  batchId: string;
  status: string;
  recordCount: number;
  importedCount: number;
  warningCount: number;
  errorCount: number;
  createdAt: string;
};

export type RuntimeSources = {
  topics: "db_imported" | "file_fallback";
  evidence: "db_imported" | "file_fallback";
};

export type ImportSummary = {
  activeTopics: number;
  activeEvidenceStudies: number;
  importBatchCount: number;
  latestBatchId: string | null;
  latestBatchStatus: string | null;
  latestByKind: Record<string, ImportSummaryKind>;
  runtimeSources: RuntimeSources;
  semanticDocuments: number;
  semanticChunks: number;
  semanticCollections: Record<string, number>;
};

export type ImportDebugConfig = {
  strictMvpPubmed: boolean;
  runtimeEngine: "deterministic" | "semantic_retrieval_lab";
  semanticRetrievalEnabled: boolean;
  retrievalMode: "hybrid" | "dense_only";
  llmImportAssistEnabled: boolean;
  llmExplainabilityEnabled: boolean;
};

export type ImportDebugLogEntry = {
  timestamp: string;
  level: string;
  event: string;
  datasetKind: string | null;
  path: string | null;
  message: string;
  details: Record<string, unknown>;
};

export type SemanticImportStatus = {
  datasetKind: "esmo" | "pubmed";
  latestBatchId: string | null;
  latestStatus: string | null;
  documentCount: number;
  chunkCount: number;
  latestJob: Record<string, unknown> | null;
};

export type EmbeddingManifest = {
  pointCount: number;
  sourceCounts: Record<string, number>;
  histologyCounts: Record<string, number>;
  embeddingModel: string;
  projectionMethod: string;
  vectorStore: string;
};

export type EmbeddingPoint = {
  pointId: string;
  chunkId: string;
  sourceType: "pubmed" | "esmo";
  sourceId: string;
  title: string;
  topicId: string | null;
  histology: string;
  x: number;
  y: number;
  label: string;
};

export type EmbeddingNeighbor = {
  pointId: string;
  title: string;
  sourceType: "pubmed" | "esmo";
  sourceId: string;
  similarity: number;
};
