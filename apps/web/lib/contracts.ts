export type VignetteInput = {
  cancerType: "NSCLC";
  diseaseSetting: "early" | "locally_advanced" | "metastatic";
  histology: "adenocarcinoma" | "squamous" | "non_squamous";
  lineOfTherapy: "first_line" | "second_line" | "later_line" | "mixed" | "unspecified";
  performanceStatus: "0" | "1" | "2" | "3" | "4";
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
  topEvidence: Array<{
    rank: number;
    evidenceId: string;
    title: string;
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
};

export type TracePayload = {
  traceId: string;
  runId: string;
  inputSchemaVersion: string;
  rulesetVersion: string;
  corpusVersion: string;
  gateCandidateCount: number;
  eligibleCount: number;
  topEvidenceCount: number;
  secondaryCount: number;
  uncertaintyFlags: string[];
  safetyFooterKey: string;
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
};

export type ImportDebugConfig = {
  strictMvpPubmed: boolean;
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
