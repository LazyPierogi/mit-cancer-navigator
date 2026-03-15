import type { EngineBenchmarkResult } from "@/lib/contracts";

export const sampleRun = {
  id: "run-demo-001",
  status: "completed" as const,
  rulesetVersion: "mvp-2026-02-28",
  corpusVersion: "canonical-frozen-pack-v2",
  createdAt: "2026-02-28T10:00:00.000Z",
  latencyMs: 412,
  engine: "deterministic" as const,
  retrievalMode: "hybrid" as const,
  vectorStore: "deterministic_only",
  embeddingModel: "none",
  chunkingStrategyVersion: "none",
  uncertaintyFlags: ["unspecified_biomarker_applicability:PMID-10002"],
  safetyFooterKey: "demo-safety-footer-v1",
  traceId: "trace-demo-001",
  topEvidence: [
    {
      rank: 1,
      evidenceId: "PMID-10001",
      title: "Pembrolizumab first-line therapy in metastatic NSCLC with PD-L1 >= 50%",
      publicationYear: 2024,
      ersTotal: 53,
      mappingLabel: "aligned" as const,
      mappedTopicId: "topic-met-nsclc-pdl1-ge50-first-line",
      mappedTopicTitle: "Metastatic NSCLC, driver-negative, PD-L1 >=50: first systemic therapy evidence",
      applicabilityNote: "Matches metastatic setting; histology adenocarcinoma.",
      abstract: "This study evaluated the efficacy of pembrolizumab as a first-line therapy in patients with metastatic non-small-cell lung cancer (NSCLC) and a PD-L1 tumor proportion score of 50% or greater. The trial demonstrated significantly longer overall survival and progression-free survival compared to platinum-based chemotherapy. The results suggest pembrolizumab is highly effective in this patient population, establishing it as a new standard of care.",
      ersBreakdown: {
        evidenceStrength: 16,
        datasetRobustness: 15,
        sourceCredibility: 12,
        recency: 10
      },
      citations: [
        {
          sourceId: "PMID-10001",
          title: "Pembrolizumab first-line therapy in metastatic NSCLC with PD-L1 >= 50%",
          year: 2024
        }
      ]
    }
  ],
  manualReviewEvidence: [
    {
      evidenceId: "PMID-10004",
      title: "Real-world NSCLC cohort with incomplete study-type metadata",
      publicationYear: 2025,
      classificationStatus: "manual_review_required" as const,
      manualReviewReason: "evidence_type_unspecified" as const,
      mappedTopicId: "topic-met-nsclc-pdl1-ge50-first-line",
      mappedTopicTitle: "Metastatic NSCLC, driver-negative, PD-L1 >=50: first systemic therapy evidence",
      mappingLabel: "guideline_silent" as const,
      potentialConflict: false,
      applicabilityNote: "Evidence type could not be reliably determined from structured source metadata. This item is shown for clinician review only and is excluded from the primary ERS ranking.",
      citations: [
        {
          sourceId: "PMID-10004",
          title: "Real-world NSCLC cohort with incomplete study-type metadata",
          year: 2025
        }
      ]
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
  ],
  retrievalCandidateCount: 0,
  semanticEvidence: [],
  semanticGuidelineCandidates: [],
  explainabilitySummary: null,
  semanticCandidateOnlyCount: 0
};

export const sampleTrace = {
  traceId: "trace-demo-001",
  runId: "run-demo-001",
  inputSchemaVersion: "v1",
  rulesetVersion: "mvp-2026-02-28",
  corpusVersion: "canonical-frozen-pack-v2",
  engine: "deterministic" as const,
  retrievalMode: "hybrid" as const,
  vectorStore: "deterministic_only",
  embeddingModel: "none",
  chunkingStrategyVersion: "none",
  gateCandidateCount: 12,
  eligibleCount: 6,
  topEvidenceCount: 1,
  manualReviewCount: 1,
  secondaryCount: 2,
  uncertaintyFlags: ["unspecified_biomarker_applicability:PMID-10002"],
  safetyFooterKey: "demo-safety-footer-v1",
  retrievalCandidateCount: 0,
  semanticCandidateOnlyCount: 0
};

export const benchmarkMetrics = [
  { label: "Recall", value: "0.95", detail: "Target >= 0.95" },
  { label: "Mapping Error", value: "0.11", detail: "Target <= 0.15" },
  { label: "Citation Error", value: "0.08", detail: "Target <= 0.15" },
  { label: "Logic Fidelity", value: "1.00", detail: "Target = 1.00" }
];

export const sampleEngineBenchmark = {
  evalRunId: "benchmark-demo-001",
  packId: "demo-presets-v3",
  summary: {
    packLabel: "MIT Demo Presets",
    semanticChangesDecisionLayer: false,
    headline: "Compare deterministic precision against hybrid semantic breadth on the same cases.",
    recommendedTakeaway:
      "Use deterministic runtime as the current decision authority, and use hybrid semantic as a live benchmark for retrieval breadth and grounded explainability.",
    benchmarkNarrative: null
  },
  meta: {
    cached: true,
    cacheKey: "sample-benchmark-fallback",
    benchmarkVersion: "sample",
    pubmedBatchId: null,
    esmoBatchId: null,
    pubmedSemanticJobId: null,
    esmoSemanticJobId: null,
    sourceFingerprint: "sample-source-fingerprint",
    runtimeConfigFingerprint: "sample-runtime-config",
    vectorStore: null,
    embeddingModel: null
  },
  engines: [
    {
      engineKey: "deterministic",
      label: "Deterministic Runtime",
      runtimeEngine: "deterministic",
      retrievalMode: "hybrid",
      status: "available",
      aggregate: {
        caseCount: 3,
        casesWithAlignedEvidence: 3,
        totalTopEvidence: 44,
        totalAligned: 24,
        totalGuidelineSilent: 20,
        totalConflict: 0,
        totalManualReview: 18,
        totalSecondary: 91,
        totalUncertaintyFlags: 39,
        totalRetrievalCandidates: 0,
        totalRetrievalCaseHits: 0,
        retrievalOverlapCount: 0,
        retrievalMultiCaseEvidenceCount: 0,
        retrievalOverlapRate: 0,
        totalSemanticCandidateOnly: 0,
        averageTopEvidence: 14.67,
        averageAligned: 8,
        averageUncertaintyFlags: 13,
        averageExpectedRecall: null,
        averageExpectedLabelAccuracy: null
      },
      cases: [
        {
          caseId: "preset-1",
          caseLabel: "MR. WAYNE",
          detail: "Metastatic adeno · 1L · PD-L1-high · pan-driver negative",
          status: "completed",
          error: null,
          metrics: {
            engine: "deterministic",
            retrievalMode: "hybrid",
            topEvidenceCount: 12,
            alignedCount: 9,
            guidelineSilentCount: 3,
            conflictCount: 0,
            manualReviewCount: 6,
            secondaryCount: 28,
            uncertaintyFlagCount: 11,
            retrievalCandidateCount: 0,
            semanticCandidateOnlyCount: 0,
            topTopicTitles: ["PD-L1 >=50 first systemic therapy evidence"],
            expectedRecall: null,
            expectedLabelAccuracy: null
          }
        },
        {
          caseId: "preset-2",
          caseLabel: "MR. STARK",
          detail: "Locally advanced squamous · post-CRT consolidation",
          status: "completed",
          error: null,
          metrics: {
            engine: "deterministic",
            retrievalMode: "hybrid",
            topEvidenceCount: 11,
            alignedCount: 6,
            guidelineSilentCount: 5,
            conflictCount: 0,
            manualReviewCount: 5,
            secondaryCount: 25,
            uncertaintyFlagCount: 13,
            retrievalCandidateCount: 0,
            semanticCandidateOnlyCount: 0,
            topTopicTitles: ["Second-line metastatic NSCLC evidence"],
            expectedRecall: null,
            expectedLabelAccuracy: null
          }
        },
        {
          caseId: "preset-3",
          caseLabel: "MRS. DOUBTFIRE",
          detail: "Early adeno · resected · adjuvant EGFR-positive",
          status: "completed",
          error: null,
          metrics: {
            engine: "deterministic",
            retrievalMode: "hybrid",
            topEvidenceCount: 21,
            alignedCount: 9,
            guidelineSilentCount: 12,
            conflictCount: 0,
            manualReviewCount: 7,
            secondaryCount: 38,
            uncertaintyFlagCount: 15,
            retrievalCandidateCount: 0,
            semanticCandidateOnlyCount: 0,
            topTopicTitles: ["EGFR-mutated first-line targeted therapy evidence"],
            expectedRecall: null,
            expectedLabelAccuracy: null
          }
        }
      ],
      notes: [
        "Deterministic runtime remains the benchmark authority for alignment labels and clinician-facing ranking."
      ]
    },
    {
      engineKey: "hybrid_semantic",
      label: "Hybrid Semantic Lab",
      runtimeEngine: "semantic_retrieval_lab",
      retrievalMode: "hybrid",
      status: "available",
      aggregate: {
        caseCount: 3,
        casesWithAlignedEvidence: 3,
        totalTopEvidence: 51,
        totalAligned: 30,
        totalGuidelineSilent: 18,
        totalConflict: 0,
        totalManualReview: 21,
        totalSecondary: 88,
        totalUncertaintyFlags: 45,
        totalRetrievalCandidates: 72,
        totalRetrievalCaseHits: 78,
        retrievalOverlapCount: 6,
        retrievalMultiCaseEvidenceCount: 5,
        retrievalOverlapRate: 0.0769,
        totalSemanticCandidateOnly: 19,
        averageTopEvidence: 17,
        averageAligned: 10,
        averageUncertaintyFlags: 15,
        averageExpectedRecall: null,
        averageExpectedLabelAccuracy: null
      },
      cases: [
        {
          caseId: "preset-1",
          caseLabel: "MR. WAYNE",
          detail: "Metastatic adeno · 1L · PD-L1-high · pan-driver negative",
          status: "completed",
          error: null,
          metrics: {
            engine: "semantic_retrieval_lab",
            retrievalMode: "hybrid",
            topEvidenceCount: 15,
            alignedCount: 11,
            guidelineSilentCount: 4,
            conflictCount: 0,
            manualReviewCount: 7,
            secondaryCount: 27,
            uncertaintyFlagCount: 13,
            retrievalCandidateCount: 24,
            semanticCandidateOnlyCount: 6,
            topTopicTitles: ["PD-L1 >=50 first systemic therapy evidence"],
            expectedRecall: null,
            expectedLabelAccuracy: null
          }
        },
        {
          caseId: "preset-2",
          caseLabel: "MR. STARK",
          detail: "Locally advanced squamous · post-CRT consolidation",
          status: "completed",
          error: null,
          metrics: {
            engine: "semantic_retrieval_lab",
            retrievalMode: "hybrid",
            topEvidenceCount: 13,
            alignedCount: 8,
            guidelineSilentCount: 5,
            conflictCount: 0,
            manualReviewCount: 6,
            secondaryCount: 24,
            uncertaintyFlagCount: 14,
            retrievalCandidateCount: 23,
            semanticCandidateOnlyCount: 6,
            topTopicTitles: ["Second-line metastatic NSCLC evidence"],
            expectedRecall: null,
            expectedLabelAccuracy: null
          }
        },
        {
          caseId: "preset-3",
          caseLabel: "MRS. DOUBTFIRE",
          detail: "Early adeno · resected · adjuvant EGFR-positive",
          status: "completed",
          error: null,
          metrics: {
            engine: "semantic_retrieval_lab",
            retrievalMode: "hybrid",
            topEvidenceCount: 23,
            alignedCount: 11,
            guidelineSilentCount: 9,
            conflictCount: 0,
            manualReviewCount: 8,
            secondaryCount: 37,
            uncertaintyFlagCount: 18,
            retrievalCandidateCount: 25,
            semanticCandidateOnlyCount: 7,
            topTopicTitles: ["EGFR-mutated first-line targeted therapy evidence"],
            expectedRecall: null,
            expectedLabelAccuracy: null
          }
        }
      ],
      notes: [
        "Hybrid Semantic Lab can now rescue sparse evidence and apply semantic topic hints before deterministic labeling closes the loop."
      ]
    }
  ],
  breakdown: {
    retrieval: {
      delta: 72,
      deterministicUniqueEvidenceCount: 0,
      hybridUniqueEvidenceCount: 72,
      hybridCaseHitCountTotal: 78,
      hybridOverlapCount: 6,
      hybridMultiCaseEvidenceCount: 5,
      hybridOverlapRate: 0.0769,
      hybridOnlyEvidenceCount: 72,
      sampleHybridOnlyEvidenceIds: ["PMID-10005", "PMID-10007", "PMID-10011"],
      sampleMultiCaseEvidenceIds: ["PMID-10021", "PMID-10034"]
    },
    decisionLayer: {
      alignedDelta: 6,
      guidelineSilentDelta: -2,
      manualReviewDelta: 3,
      promotedAlignedUniqueCount: 5,
      promotedGuidelineSilentUniqueCount: 1,
      promotedManualReviewUniqueCount: 3,
      samplePromotedAlignedEvidenceIds: ["PMID-10005", "PMID-10011"],
      samplePromotedGuidelineSilentEvidenceIds: ["PMID-10017"],
      samplePromotedManualReviewEvidenceIds: ["PMID-10023", "PMID-10034"]
    },
    caseDeltas: [
      {
        caseId: "preset-1",
        caseLabel: "MR. WAYNE",
        retrievalDelta: 24,
        alignedDelta: 2,
        guidelineSilentDelta: 1,
        manualReviewDelta: 1,
        hybridRetrievalCount: 24,
        hybridOnlyRetrievalCount: 24,
        promotedAlignedCount: 2,
        promotedGuidelineSilentCount: 1,
        promotedManualReviewCount: 1,
        sampleRetrievalEvidenceIds: ["PMID-10005", "PMID-10007"],
        sampleHybridOnlyRetrievalEvidenceIds: ["PMID-10005", "PMID-10007"],
        samplePromotedAlignedEvidenceIds: ["PMID-10005"],
        samplePromotedGuidelineSilentEvidenceIds: ["PMID-10017"],
        samplePromotedManualReviewEvidenceIds: ["PMID-10023"]
      },
      {
        caseId: "preset-2",
        caseLabel: "MR. STARK",
        retrievalDelta: 23,
        alignedDelta: 2,
        guidelineSilentDelta: 0,
        manualReviewDelta: 1,
        hybridRetrievalCount: 23,
        hybridOnlyRetrievalCount: 23,
        promotedAlignedCount: 2,
        promotedGuidelineSilentCount: 0,
        promotedManualReviewCount: 1,
        sampleRetrievalEvidenceIds: ["PMID-10011", "PMID-10019"],
        sampleHybridOnlyRetrievalEvidenceIds: ["PMID-10011", "PMID-10019"],
        samplePromotedAlignedEvidenceIds: ["PMID-10011"],
        samplePromotedGuidelineSilentEvidenceIds: [],
        samplePromotedManualReviewEvidenceIds: ["PMID-10034"]
      },
      {
        caseId: "preset-3",
        caseLabel: "MRS. DOUBTFIRE",
        retrievalDelta: 25,
        alignedDelta: 2,
        guidelineSilentDelta: -3,
        manualReviewDelta: 1,
        hybridRetrievalCount: 25,
        hybridOnlyRetrievalCount: 25,
        promotedAlignedCount: 2,
        promotedGuidelineSilentCount: 0,
        promotedManualReviewCount: 1,
        sampleRetrievalEvidenceIds: ["PMID-10021", "PMID-10034"],
        sampleHybridOnlyRetrievalEvidenceIds: ["PMID-10021", "PMID-10034"],
        samplePromotedAlignedEvidenceIds: ["PMID-10029"],
        samplePromotedGuidelineSilentEvidenceIds: [],
        samplePromotedManualReviewEvidenceIds: ["PMID-10041"]
      }
    ]
  },
  notes: [
    "This fallback benchmark mirrors the live product story: deterministic owns final labels, semantic broadens the candidate set.",
    "Use it when the API is unavailable so the LAB tab still demos the hybrid benchmark narrative."
  ]
} as EngineBenchmarkResult;

export const sampleImportSummary = {
  activeTopics: 10,
  activeEvidenceStudies: 9,
  importBatchCount: 4,
  latestBatchId: "import-pubmed-demo-20260307",
  latestBatchStatus: "completed_with_warnings",
  latestByKind: {
    esmo: {
      batchId: "import-esmo-demo-20260307",
      status: "completed",
      recordCount: 10,
      importedCount: 10,
      warningCount: 0,
      errorCount: 0,
      createdAt: "2026-03-07T09:20:00.000Z"
    },
    pubmed: {
      batchId: "import-pubmed-demo-20260307",
      status: "completed_with_warnings",
      recordCount: 9,
      importedCount: 9,
      warningCount: 1,
      errorCount: 0,
      createdAt: "2026-03-07T09:31:00.000Z"
    }
  },
  runtimeSources: {
    topics: "db_imported" as const,
    evidence: "db_imported" as const
  },
  semanticDocuments: 0,
  semanticChunks: 0,
  semanticCollections: {}
};

export const sampleImportDebugConfig = {
  strictMvpPubmed: false,
  runtimeEngine: "deterministic" as const,
  semanticRetrievalEnabled: false,
  retrievalMode: "hybrid" as const,
  llmImportAssistEnabled: false,
  llmExplainabilityEnabled: false
};

export const sampleImportDebugLogs = [
  {
    timestamp: "2026-03-07T09:31:11.000Z",
    level: "warning",
    event: "import_completed",
    datasetKind: "pubmed",
    path: "/datasets/pubmed/evidence.curated.json",
    message: "Import completed with 1 warning.",
    details: {
      batchId: "import-pubmed-demo-20260307",
      strictMvpPubmed: false,
      warningCount: 1,
      runtimeEngine: "deterministic"
    }
  },
  {
    timestamp: "2026-03-07T09:30:52.000Z",
    level: "info",
    event: "import_started",
    datasetKind: "pubmed",
    path: "/datasets/pubmed/evidence.curated.json",
    message: "Import requested.",
    details: {
      strictMvpPubmed: false,
      runtimeEngine: "deterministic"
    }
  },
  {
    timestamp: "2026-03-07T09:20:14.000Z",
    level: "info",
    event: "import_completed",
    datasetKind: "esmo",
    path: "/datasets/esmo/topics.curated.json",
    message: "Import completed.",
    details: {
      batchId: "import-esmo-demo-20260307",
      strictMvpPubmed: false,
      warningCount: 0,
      runtimeEngine: "deterministic"
    }
  }
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
  { caseId: "V4", reviewer: "Federico", status: "delta review pending" },
  { caseId: "V11", reviewer: "Team", status: "conflict check pending" },
  { caseId: "V13", reviewer: "Team", status: "ready for scoring" }
];

export const datasets = [
  { id: "esmo-curated-preview-v1", source: "ESMO topic pack", status: "preview-ready", records: 10 },
  { id: "pubmed-curated-preview-v1", source: "Curated PubMed evidence", status: "preview-ready", records: 9 },
  { id: "frozen-pack-canonical-v2", source: "Frozen vignette pack", status: "canonical", records: 15 }
];
