export type VignetteInput = {
  cancerType: "NSCLC";
  diseaseSetting: "early" | "locally_advanced" | "metastatic";
  histology: "adenocarcinoma" | "squamous";
  performanceStatus: "0" | "1" | "2" | "3" | "4";
  biomarkers: {
    EGFR: "yes" | "no";
    ALK: "yes" | "no";
    ROS1: "yes" | "no";
    PDL1Bucket: "lt1" | "1to49" | "ge50";
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

