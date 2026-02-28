export const sampleRun = {
  id: "run-demo-001",
  rulesetVersion: "mvp-2026-02-28",
  corpusVersion: "sample-corpus-v1",
  uncertaintyFlags: ["unspecified_biomarker_applicability:PMID-10002"],
  topEvidence: [
    {
      rank: 1,
      evidenceId: "PMID-10001",
      title: "Pembrolizumab first-line therapy in metastatic NSCLC with PD-L1 >= 50%",
      ersTotal: 53,
      mappingLabel: "aligned",
      mappedTopicTitle: "Metastatic NSCLC, driver-negative, PD-L1 >=50: first systemic therapy evidence",
      applicabilityNote: "Matches metastatic setting; histology adenocarcinoma.",
      ersBreakdown: {
        evidenceStrength: 16,
        datasetRobustness: 15,
        sourceCredibility: 12,
        recency: 10
      }
    }
  ],
  secondaryReferences: [
    {
      evidenceId: "PMID-10002",
      exclusionReasons: ["below_top_evidence_threshold:24"]
    },
    {
      evidenceId: "PMID-10003",
      exclusionReasons: ["biomarker_mismatch:EGFR"]
    }
  ]
};

export const benchmarkMetrics = [
  { label: "Recall", value: "0.95", detail: "Target >= 0.95" },
  { label: "Mapping Error", value: "0.11", detail: "Target <= 0.15" },
  { label: "Citation Error", value: "0.08", detail: "Target <= 0.15" },
  { label: "Logic Fidelity", value: "1.00", detail: "Target = 1.00" }
];

export const policy = {
  safetyBoundaries: [
    "Not diagnosis",
    "Not prescribing",
    "Not replacing clinician judgment",
    "No exhaustive evidence claims",
    "No inference beyond provided inputs"
  ],
  hardStops: [
    "Recommendation language",
    "Approval or allowance claims",
    "Misclassification regression",
    "Removed uncertainty disclosures"
  ]
};

export const reviewerQueue = [
  { caseId: "VIG-001", reviewer: "Federico", status: "subset review pending" },
  { caseId: "VIG-002", reviewer: "Team", status: "citation check pending" },
  { caseId: "VIG-003", reviewer: "Team", status: "ready for scoring" }
];

export const datasets = [
  { id: "esmo-v1", source: "ESMO topic pack", status: "ready", records: 12 },
  { id: "pubmed-v1", source: "Curated PubMed evidence", status: "ready", records: 48 },
  { id: "frozen-pack-v1", source: "Frozen vignette pack", status: "ready", records: 15 }
];

