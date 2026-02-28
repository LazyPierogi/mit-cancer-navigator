PREREQ (data prepared, not runtime)
  [PDF/Text Evidence Docs] + [Guideline Snippet Docs]
        |
        v
  [Text Extraction + Cleaning]
        |
        v
  [Chunking]
   - split by headings/paragraphs
   - context-aware boundaries (no mid-sentence)
   - overlap small (configurable)
   - attach metadata: doc_id, section, page, doi/url
        |
        v
  [Embeddings]
   - dense embeddings
   - sparse embeddings (for hybrid)
        |
        v
  [QDRANT Upsert]
   - evidence_chunks collection
   - guideline_snippets collection

RUNTIME
[Patient Vignette JSON]
  - NSCLC fields (stage, histology, biomarkers, therapy line, etc.)
        |
        v
[Query Builder + Normalizer]
  Knobs:
    SUBQUERIES=3..5
    QUERY_EXPANSION=on/off
        |
        +-----------------------------------------------+
        |                                               |
        v                                               v
[QDRANT Evidence Retrieval]                       [QDRANT Guideline Retrieval]
  Collection: evidence_chunks                      Collection: guideline_snippets
  Knobs:
    HYBRID_MODE=dense or dense+sparse              HYBRID_MODE=dense or dense+sparse
    TOPK_RETRIEVE_EVIDENCE=30..80                  TOPK_RETRIEVE_GUIDELINES=5..20
    FUSION_METHOD=RRF                              FUSION_METHOD=RRF
    RRF_K=60 (tunuj)                               RRF_K=60 (tunuj)
        |                                               |
        v                                               v
[Rerank + Dedup + Cluster]                        [Rerank + Dedup]
  Knobs:
    TOPK_RERANK_EVIDENCE=20..40                    TOPK_RERANK_GUIDELINES=5..15
    TOPK_FINAL_EVIDENCE=5..10                      TOPK_FINAL_GUIDELINES=1..3
    DEDUP_SIM_THRESHOLD=0.85                       DEDUP_SIM_THRESHOLD=0.85
  Output:
    evidence set (chunks + citations)              guideline set (snippets + refs)
        |                                               |
        +-------------------------+---------------------+
                                  v
                    [Pairing + LABELING Engine]
                      Knobs:
                        PAIRING_STRATEGY=one-to-many
                        EVIDENCE_PER_GUIDELINE=3
                        LABELER_TYPE=NLI-like
                        CONF_THRESHOLD=0.65 (example)
                        MAX_JUSTIFICATION_TOKENS=120
                        CITATION_REQUIRED=on
                                  |
                                  v
                          [Output UI / API]
                            - vignette summary
                            - guideline snippet(s)
                            - evidence chunks with citations
                            - label aligned/conflict/silent + confidence
                            - timeouts + cache