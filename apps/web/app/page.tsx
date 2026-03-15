"use client";

import React, { useState, useEffect, useRef } from 'react';
import { UserCircle, Lock, Plus, AlertTriangle, FlaskConical, Award, ShieldCheck, ArrowRight, ClipboardCheck, Info, Eraser } from 'lucide-react';
import { STYLES } from '@/lib/theme';
import { EvidenceCard, ManualReviewCard, StatBadge } from '@/components/EvidenceCard';
import { StanceMatrix } from '@/components/StanceMatrix';
import { PolicyStrip } from '@/components/PolicyStrip';
import { createRun, getImportDebugConfig, prewarmRuntime, updateImportDebugConfig } from '@/lib/api';
import { individualPresets } from '@/lib/presets';
import type { VignetteInput, AnalyzeRunResponse, ImportDebugConfig } from '@/lib/contracts';
import { readNavigatorDebugPreferences, subscribeNavigatorDebugPreferences } from '@/lib/debug-preferences';
import { readNavigatorSessionState, writeNavigatorSessionState } from '@/lib/navigator-session';

const DISEASE_SETTING_OPTIONS = [
  { label: "Early", value: "early" as const },
  { label: "Locally Advanced", value: "locally_advanced" as const },
  { label: "Metastatic", value: "metastatic" as const }
];

const HISTOLOGY_OPTIONS = [
  { label: "Adenocarcinoma", value: "adenocarcinoma" as const },
  { label: "Squamous Cell", value: "squamous" as const },
  { label: "Non Squamous", value: "non_squamous" as const }
];

const BIOMARKERS = [
  { label: "EGFR+", key: "EGFR", val: "yes" as const },
  { label: "ALK+", key: "ALK", val: "yes" as const },
  { label: "ROS1+", key: "ROS1", val: "yes" as const },
  { label: "PD-L1 ≥ 50%", key: "PDL1Bucket", val: "ge50" as const },
  { label: "Wild Type", key: "EGFR", val: "no" as const } // Simplification for demo
];

const LINES_OF_THERAPY = [
  { label: "1st Line", value: "first_line" as const },
  { label: "2nd Line", value: "second_line" as const },
  { label: "Later Line", value: "later_line" as const },
  { label: "Adjuvant", value: "adjuvant" as const },
  { label: "Consolidation", value: "consolidation" as const }
];

const PERFORMANCE_STATUS_OPTIONS = ["0", "1", "2", "3", "4"] as const;

const fingerprintVignette = (value: VignetteInput) => JSON.stringify(value);

type EvidenceSortMode = "alignment" | "recency" | "ers";

const alignmentPriority: Record<AnalyzeRunResponse['topEvidence'][0]['mappingLabel'], number> = {
  aligned: 0,
  guideline_silent: 1,
  conflict: 2,
};

const sortTopEvidence = (items: AnalyzeRunResponse['topEvidence'], sortMode: EvidenceSortMode) => {
  const sorted = [...items];

  sorted.sort((a, b) => {
    if (sortMode === "recency") {
      return (
        (b.publicationYear ?? 0) - (a.publicationYear ?? 0) ||
        b.ersTotal - a.ersTotal ||
        alignmentPriority[a.mappingLabel] - alignmentPriority[b.mappingLabel] ||
        a.rank - b.rank ||
        a.evidenceId.localeCompare(b.evidenceId)
      );
    }

    if (sortMode === "ers") {
      return (
        b.ersTotal - a.ersTotal ||
        alignmentPriority[a.mappingLabel] - alignmentPriority[b.mappingLabel] ||
        (b.publicationYear ?? 0) - (a.publicationYear ?? 0) ||
        a.rank - b.rank ||
        a.evidenceId.localeCompare(b.evidenceId)
      );
    }

    return (
      alignmentPriority[a.mappingLabel] - alignmentPriority[b.mappingLabel] ||
      b.ersTotal - a.ersTotal ||
      (b.publicationYear ?? 0) - (a.publicationYear ?? 0) ||
      a.rank - b.rank ||
      a.evidenceId.localeCompare(b.evidenceId)
    );
  });

  return sorted;
};

export default function HomePage() {
  const [activePresetId, setActivePresetId] = useState<string>(individualPresets[0].id);
  const [vignette, setVignette] = useState<VignetteInput>(individualPresets[0].vignette);
  const [customInput, setCustomInput] = useState("");
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [runResponse, setRunResponse] = useState<AnalyzeRunResponse | null>(null);
  const [lastPolicyRunResponse, setLastPolicyRunResponse] = useState<AnalyzeRunResponse | null>(null);
  const [lastAnalyzedFingerprint, setLastAnalyzedFingerprint] = useState("");
  const [showClinicalModifiers, setShowClinicalModifiers] = useState(false);
  const [sortMode, setSortMode] = useState<EvidenceSortMode>("alignment");
  const [debugConfig, setDebugConfig] = useState<ImportDebugConfig>({
    strictMvpPubmed: false,
    runtimeEngine: "deterministic",
    semanticRetrievalEnabled: false,
    retrievalMode: "hybrid",
    llmImportAssistEnabled: false,
    llmExplainabilityEnabled: false
  });
  const [isSavingDebugConfig, setIsSavingDebugConfig] = useState(false);
  const [isNavigatorSessionBootstrapped, setIsNavigatorSessionBootstrapped] = useState(false);
  const manualReviewSectionRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const restored = readNavigatorSessionState();
    if (restored) {
      setActivePresetId(restored.activePresetId);
      setVignette(restored.vignette);
      setCustomInput(restored.customInput);
      setRunResponse(restored.runResponse);
      setLastPolicyRunResponse(restored.lastPolicyRunResponse ?? restored.runResponse);
      setLastAnalyzedFingerprint(restored.lastAnalyzedFingerprint);
      setSortMode(restored.sortMode);
      setIsNavigatorSessionBootstrapped(true);
      return;
    }

    void handleRun(individualPresets[0].vignette);
    setIsNavigatorSessionBootstrapped(true);
  }, []);

  useEffect(() => {
    if (!isNavigatorSessionBootstrapped) {
      return;
    }

    writeNavigatorSessionState({
      activePresetId,
      vignette,
      customInput,
      runResponse,
      lastPolicyRunResponse,
      lastAnalyzedFingerprint,
      sortMode,
    });
  }, [activePresetId, customInput, isNavigatorSessionBootstrapped, lastAnalyzedFingerprint, lastPolicyRunResponse, runResponse, sortMode, vignette]);

  useEffect(() => {
    setShowClinicalModifiers(readNavigatorDebugPreferences().showClinicalModifiers);
    return subscribeNavigatorDebugPreferences((next) => {
      setShowClinicalModifiers(next.showClinicalModifiers);
    });
  }, []);

  useEffect(() => {
    let mounted = true;

    async function loadDebugConfig() {
      const nextConfig = await getImportDebugConfig();
      if (mounted) {
        setDebugConfig(nextConfig);
      }
    }

    function handleWindowFocus() {
      void loadDebugConfig();
    }

    function handleVisibilityChange() {
      if (document.visibilityState === "visible") {
        void loadDebugConfig();
      }
    }

    void loadDebugConfig();
    window.addEventListener("focus", handleWindowFocus);
    document.addEventListener("visibilitychange", handleVisibilityChange);

    return () => {
      mounted = false;
      window.removeEventListener("focus", handleWindowFocus);
      document.removeEventListener("visibilitychange", handleVisibilityChange);
    };
  }, []);

  useEffect(() => {
    if (!debugConfig.semanticRetrievalEnabled && !debugConfig.llmExplainabilityEnabled) {
      return;
    }
    void prewarmRuntime({ includeSemantic: true });
  }, [debugConfig.llmExplainabilityEnabled, debugConfig.semanticRetrievalEnabled]);

  const persistImportConfig = async (
    updates: Partial<ImportDebugConfig>,
    options?: { rerunCurrentVignette?: boolean }
  ) => {
    setIsSavingDebugConfig(true);
    try {
      const nextConfig = await updateImportDebugConfig({ ...debugConfig, ...updates });
      setDebugConfig(nextConfig);
      if (options?.rerunCurrentVignette) {
        await handleRun(vignette);
      }
    } finally {
      setIsSavingDebugConfig(false);
    }
  };

  const handleClearResults = () => {
    setRunResponse(null);
    setLastAnalyzedFingerprint("");
    setSortMode("alignment");
  };

  const handleRun = async (payload: VignetteInput) => {
    setIsAnalyzing(true);
    try {
      const res = await createRun(payload);
      setRunResponse(res);
      setLastPolicyRunResponse(res);
      setLastAnalyzedFingerprint(fingerprintVignette(payload));
    } catch (err) {
      console.error(err);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handlePresetChange = (presetId: string) => {
    const preset = individualPresets.find(p => p.id === presetId)!;
    setActivePresetId(preset.id);
    setVignette(preset.vignette);
  };

  const updateDiseaseSetting = (value: VignetteInput["diseaseSetting"]) => {
    setActivePresetId("");
    setVignette((current) => ({
      ...current,
      diseaseSetting: value,
      diseaseStage: value === "metastatic" ? "stage_iv" : value === "locally_advanced" ? "stage_iii" : "unspecified",
      resectabilityStatus:
        value === "metastatic"
          ? "not_applicable"
          : current.lineOfTherapy === "adjuvant"
            ? "resected"
            : current.lineOfTherapy === "consolidation"
              ? "unresectable"
              : "unspecified",
    }));
  };

  const updateLineOfTherapy = (value: VignetteInput["lineOfTherapy"]) => {
    setActivePresetId("");
    setVignette((current) => ({
      ...current,
      lineOfTherapy: value,
      diseaseSetting:
        value === "adjuvant"
          ? "early"
          : value === "consolidation"
            ? "locally_advanced"
            : current.diseaseSetting,
      diseaseStage:
        value === "consolidation"
          ? "stage_iii"
          : value === "adjuvant"
            ? "unspecified"
            : current.diseaseStage,
      resectabilityStatus:
        value === "adjuvant"
          ? "resected"
          : value === "consolidation"
            ? "unresectable"
            : current.resectabilityStatus,
      treatmentContext:
        value === "adjuvant"
          ? "post_surgery"
          : value === "consolidation"
            ? "post_chemoradiation"
            : current.treatmentContext
    }));
  };

  const updateVignette = (updates: Partial<VignetteInput>) => {
    setActivePresetId("");
    const next = { ...vignette, ...updates };
    setVignette(next);
  };

  const setBiomarker = (key: string, val: string) => {
    setActivePresetId("");
    const next = {
      ...vignette,
      biomarkers: {
        ...vignette.biomarkers,
        [key]: val
      }
    };
    setVignette(next);
  };

  const topEvidence = sortTopEvidence(runResponse?.topEvidence || [], sortMode);
  const manualReviewEvidence = runResponse?.manualReviewEvidence || [];
  const potentialConflictReviewCount = manualReviewEvidence.filter((item) => item.potentialConflict).length;
  const alignedCount = topEvidence.filter((item) => item.mappingLabel === "aligned").length;
  const guidelineSilentCount = topEvidence.filter((item) => item.mappingLabel === "guideline_silent").length;
  const conflictCount = topEvidence.filter((item) => item.mappingLabel === "conflict").length;
  const avgErs = topEvidence.length > 0 ? (topEvidence.reduce((acc, a) => acc + a.ersTotal, 0) / topEvidence.length).toFixed(1) : "0.0";
  const hasPendingChanges = lastAnalyzedFingerprint !== "" && fingerprintVignette(vignette) !== lastAnalyzedFingerprint;
  const currentRunId = runResponse?.run.id ?? "run-unavailable";
  const policyStripResponse = runResponse ?? lastPolicyRunResponse;
  const retrievedLabel = `${topEvidence.length} Studies`;
  const manualReviewLabel = `${manualReviewEvidence.length} Items`;
  const scrollToManualReviewSection = () => {
    if (!manualReviewSectionRef.current) {
      return;
    }
    const sectionTop = manualReviewSectionRef.current.getBoundingClientRect().top + window.scrollY;
    window.scrollTo({
      top: Math.max(sectionTop - 112, 0),
      behavior: "smooth",
    });
  };

  return (
    <div className="grid grid-cols-12 gap-10">
      {/* Left: Patient Profile Input */}
      <aside className="col-span-12 lg:col-span-4 space-y-8">
        <section className={`${STYLES.surface} p-8 ${STYLES.radiusMain} ${STYLES.shadow} border-0 transition-all`}>
          <div className="flex items-center justify-between mb-8">
            <h2 className={`text-sm font-bold ${STYLES.textMain} uppercase tracking-[0.1em] flex items-center gap-3`}>
              <UserCircle size={22} className={STYLES.textMuted} strokeWidth={1.5} />
              Patient Profile
            </h2>
            <Lock size={16} className={STYLES.textLight} />
          </div>

          {/* Presets Grid */}
          <div className="mb-10">
            <label className={`text-[10px] font-bold ${STYLES.textLight} uppercase tracking-widest mb-3 block`}>Navigator Presets</label>
            <div className="grid grid-cols-3 gap-3">
              {individualPresets.map(preset => (
                <button
                  key={preset.id}
                  onClick={() => handlePresetChange(preset.id)}
                  className={`flex flex-col items-center justify-center p-3 ${STYLES.radiusCard} border transition-all duration-300 ${activePresetId === preset.id ? `${STYLES.accentBg} text-white border-transparent ${STYLES.shadow}` : `${STYLES.bg} ${STYLES.textMuted} ${STYLES.borderLight} ${STYLES.hoverBg}`}`}
                >
                  <span className="text-xs font-bold uppercase tracking-wide">{preset.name}</span>
                  <span className={`text-[9px] mt-0.5 text-center leading-relaxed ${activePresetId === preset.id ? 'text-white/80' : STYLES.textLight}`}>
                    {preset.detail}
                  </span>
                </button>
              ))}
            </div>
          </div>

          <div className={`h-px w-full ${STYLES.borderLight} mb-8`} />

          {/* Explicit Tag Selection */}
          <div className={`space-y-8 ${isAnalyzing ? 'opacity-50 pointer-events-none' : ''} transition-opacity duration-300`}>
            <div className="space-y-3">
              <label className={`text-[11px] font-bold ${STYLES.textLight} uppercase tracking-widest`}>Disease Setting</label>
              <div className="flex flex-wrap gap-2.5">
                {DISEASE_SETTING_OPTIONS.map(opt => (
                  <button
                    key={opt.value}
                    onClick={() => updateDiseaseSetting(opt.value)}
                    className={`px-4 py-2 ${STYLES.radiusChip} text-xs transition-all font-medium border ${vignette.diseaseSetting === opt.value ? `${STYLES.accentBg} text-white border-transparent ${STYLES.shadow}` : `${STYLES.surface} ${STYLES.textMuted} ${STYLES.borderLight} ${STYLES.hoverBg}`}`}
                  >
                    {opt.label}
                  </button>
                ))}
              </div>
            </div>

            <div className="space-y-3">
              <label className={`text-[11px] font-bold ${STYLES.textLight} uppercase tracking-widest`}>Histology</label>
              <div className="flex flex-wrap gap-2.5">
                {HISTOLOGY_OPTIONS.map(opt => (
                  <button
                    key={opt.value}
                    onClick={() => updateVignette({ histology: opt.value })}
                    className={`px-4 py-2 ${STYLES.radiusChip} text-xs transition-all font-medium border ${vignette.histology === opt.value ? `${STYLES.accentBg} text-white border-transparent ${STYLES.shadow}` : `${STYLES.surface} ${STYLES.textMuted} ${STYLES.borderLight} ${STYLES.hoverBg}`}`}
                  >
                    {opt.label}
                  </button>
                ))}
              </div>
            </div>

            <div className="space-y-3">
              <label className={`text-[11px] font-bold ${STYLES.textLight} uppercase tracking-widest`}>Biomarker Profile</label>
              <div className="flex flex-wrap gap-2.5">
                {BIOMARKERS.map(opt => {
                  // simple check
                  const active = (vignette.biomarkers as any)[opt.key] === opt.val;
                  return (
                    <button
                      key={opt.label}
                      onClick={() => setBiomarker(opt.key, opt.val)}
                      className={`px-4 py-2 ${STYLES.radiusChip} text-xs transition-all font-medium border ${active ? `${STYLES.accentBg} text-white border-transparent ${STYLES.shadow}` : `${STYLES.surface} ${STYLES.textMuted} ${STYLES.borderLight} ${STYLES.hoverBg}`}`}
                    >
                      {opt.label}
                    </button>
                  );
                })}
              </div>
            </div>

            <div className="space-y-3">
              <label className={`text-[11px] font-bold ${STYLES.textLight} uppercase tracking-widest`}>Line of Therapy</label>
              <div className="flex flex-wrap gap-2.5">
                {LINES_OF_THERAPY.map(opt => (
                  <button
                    key={opt.value}
                    onClick={() => updateLineOfTherapy(opt.value)}
                    className={`px-4 py-2 ${STYLES.radiusChip} text-xs transition-all font-medium border ${vignette.lineOfTherapy === opt.value ? `${STYLES.accentBg} text-white border-transparent ${STYLES.shadow}` : `${STYLES.surface} ${STYLES.textMuted} ${STYLES.borderLight} ${STYLES.hoverBg}`}`}
                  >
                    {opt.label}
                  </button>
                ))}
              </div>
            </div>

            {showClinicalModifiers ? (
              <div className="space-y-4 pt-2">
                <div className="flex items-center justify-between gap-3">
                  <label className={`text-[11px] font-bold ${STYLES.textLight} uppercase tracking-widest`}>Additional Clinical Modifiers</label>
                  <span className="text-[10px] font-bold uppercase tracking-[0.18em] text-[#8A5A13] bg-[#F6E7C8] px-2.5 py-1 rounded-full">
                    Debug View
                  </span>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <label className="space-y-2">
                    <span className={`text-[10px] font-bold ${STYLES.textLight} uppercase tracking-widest`}>ECOG</span>
                    <select
                      value={vignette.performanceStatus}
                      onChange={(event) => updateVignette({ performanceStatus: event.target.value as VignetteInput["performanceStatus"] })}
                      className={`w-full ${STYLES.bg} border ${STYLES.border} ${STYLES.textMain} ${STYLES.radiusCard} px-3 py-3 text-sm font-medium focus:ring-1 ${STYLES.ring} focus:border-[#C96557] outline-none transition-all`}
                    >
                      {PERFORMANCE_STATUS_OPTIONS.map((value) => (
                        <option key={value} value={value}>PS {value}</option>
                      ))}
                    </select>
                  </label>
                  <label className="space-y-2">
                    <span className={`text-[10px] font-bold ${STYLES.textLight} uppercase tracking-widest`}>Freeform Note</span>
                    <div className="relative group">
                      <div className={`absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none ${STYLES.textLight}`}>
                        <Plus size={14} />
                      </div>
                      <input
                        type="text"
                        placeholder="Cachexia, liver mets..."
                        value={customInput}
                        onChange={(e) => setCustomInput(e.target.value)}
                        className={`w-full ${STYLES.bg} border ${STYLES.border} ${STYLES.textMain} ${STYLES.radiusCard} pl-9 pr-3 py-3 text-sm font-medium focus:ring-1 ${STYLES.ring} focus:border-[#C96557] outline-none transition-all placeholder:font-normal placeholder:opacity-60`}
                      />
                    </div>
                  </label>
                </div>
              </div>
            ) : null}
          </div>

          {showClinicalModifiers && hasPendingChanges ? (
            <div className={`mt-6 p-4 ${STYLES.radiusCard} bg-[#F9F8F6] border ${STYLES.borderLight}`}>
              <p className="text-[11px] leading-relaxed font-semibold text-[#6B6B6B]">
                Filters changed. The results on the right still show the previous run until you press <strong>Run Analysis</strong>.
              </p>
            </div>
          ) : null}

          <button
            onClick={() => handleRun(vignette)}
            disabled={isAnalyzing}
            className={`w-full py-4 mt-8 ${STYLES.accentBg} text-white font-bold uppercase tracking-widest ${STYLES.radiusCard} ${STYLES.shadow} hover:opacity-90 transition-opacity flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed`}
          >
            {isAnalyzing ? "Analyzing..." : hasPendingChanges ? "Apply Filters & Run Analysis" : "Run Analysis"}
          </button>

          {showClinicalModifiers ? (
            <div className={`mt-8 p-5 ${STYLES.radiusCard} bg-[#FBEAE5] text-[#A63D2F]`}>
              <div className="flex gap-4">
                <AlertTriangle size={20} className="shrink-0 opacity-80" strokeWidth={1.5} />
                <p className="text-[11px] leading-relaxed font-medium">
                  <strong>{runResponse?.engine === "semantic_retrieval_lab" ? "SEMANTIC RETRIEVAL LAB:" : "DETERMINISTIC MODE:"}</strong>{" "}
                  {runResponse?.engine === "semantic_retrieval_lab"
                    ? "Semantic retrieval expands candidate recall and explainability, but final labels still stay under deterministic guardrails."
                    : "Unstructured text input is restricted to keyword extraction. Any evidence failing to match all mandatory patient tags will be discarded automatically."}
                </p>
              </div>
            </div>
          ) : null}
        </section>
      </aside>

      {/* Center: Evidence and Analysis */}
      <div className="col-span-12 lg:col-span-8 space-y-10">
        {policyStripResponse && (
          <PolicyStrip
            runId={policyStripResponse.run.id}
            rulesetVersion={policyStripResponse.run.rulesetVersion}
            corpusVersion={policyStripResponse.run.corpusVersion}
            uncertaintyFlags={policyStripResponse.uncertaintyFlags}
            engine={policyStripResponse.engine}
            debugConfig={debugConfig}
            isSavingDebugConfig={isSavingDebugConfig}
            onSemanticRetrievalToggle={() =>
              void persistImportConfig(
                debugConfig.semanticRetrievalEnabled
                  ? {
                      semanticRetrievalEnabled: false,
                      runtimeEngine: "deterministic"
                    }
                  : {
                      semanticRetrievalEnabled: true,
                      runtimeEngine: "semantic_retrieval_lab"
                    },
                { rerunCurrentVignette: true }
              )
            }
            onLlmExplainabilityToggle={() =>
              void persistImportConfig(
                { llmExplainabilityEnabled: !debugConfig.llmExplainabilityEnabled },
                { rerunCurrentVignette: true }
              )
            }
          />
        )}

        {/* Summary Dashboard */}
        <div className="flex flex-wrap items-center gap-5">
            <StatBadge icon={FlaskConical} label="Retrieved" value={retrievedLabel} accentColor={STYLES.primaryText} />
            <StatBadge icon={Award} label="Avg ERS" value={avgErs} accentColor="text-[#6B6B6B]" />
            <StatBadge icon={ShieldCheck} label="Aligned" value={alignedCount} accentColor="text-[#2D5940]" valueColor="text-[#2D5940]" />
            <StatBadge icon={Info} label="Silent" value={guidelineSilentCount} accentColor="text-[#6B6B6B]" valueColor="text-[#6B6B6B]" />
            <StatBadge icon={AlertTriangle} label="Conflict" value={conflictCount} accentColor="text-[#A63D2F]" valueColor="text-[#A63D2F]" />
            <StatBadge
              icon={ClipboardCheck}
              label="Manual Review"
              value={manualReviewLabel}
              accentColor="text-[#8A5A13]"
              valueColor="text-[#8A5A13]"
              onClick={manualReviewEvidence.length > 0 ? scrollToManualReviewSection : undefined}
            />
            {runResponse?.engine === "semantic_retrieval_lab" && (
              <StatBadge icon={FlaskConical} label="Semantic Chunks" value={runResponse.retrievalCandidateCount} accentColor="text-[#A63D2F]" />
            )}

            <div className="ml-auto flex items-center gap-3">
              <span className={`text-[10px] font-bold ${STYLES.textLight} uppercase tracking-widest`}>Sorted By</span>
              <select
                value={sortMode}
                onChange={(event) => setSortMode(event.target.value as EvidenceSortMode)}
                className={`bg-transparent text-xs font-bold ${STYLES.primaryText} outline-none cursor-pointer hover:underline appearance-none`}
              >
                <option value="alignment">ALIGNMENT</option>
                <option value="recency">RECENCY</option>
                <option value="ers">ERS SCORE (DESC)</option>
              </select>
            </div>
          </div>

        {runResponse?.engine === "semantic_retrieval_lab" && runResponse.explainabilitySummary ? (
          <section className={`${STYLES.surface} ${STYLES.radiusMain} ${STYLES.shadow} border-0 p-6`}>
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div>
                <h3 className={`text-sm font-bold ${STYLES.textMain} uppercase tracking-wide`}>Semantic Retrieval Lab</h3>
                <p className={`text-[11px] ${STYLES.textLight} font-semibold mt-1 uppercase tracking-widest`}>
                  {runResponse.retrievalMode === "hybrid" ? "Hybrid retrieval" : "Dense-only retrieval"} · {runResponse.vectorStore}
                </p>
              </div>
              <span className="rounded-full bg-[#FBEAE5] px-3 py-1.5 text-[10px] font-bold uppercase tracking-[0.16em] text-[#A63D2F]">
                Candidate-only topics: {runResponse.semanticCandidateOnlyCount}
              </span>
            </div>
            <p className={`mt-4 text-sm ${STYLES.textMain} leading-relaxed`}>{runResponse.explainabilitySummary.summary}</p>
            {runResponse.semanticGuidelineCandidates.length > 0 ? (
              <div className="mt-4 flex flex-wrap gap-2">
                {runResponse.semanticGuidelineCandidates.map((candidate) => (
                  <span
                    key={candidate.topicId}
                    className="rounded-full border border-[#E9B7AC] bg-[#FFF5F1] px-3 py-1.5 text-[10px] font-bold uppercase tracking-[0.16em] text-[#8B3E2F]"
                  >
                    {candidate.topicTitle}
                  </span>
                ))}
              </div>
            ) : null}
          </section>
        ) : null}

        {/* Results List */}
        <div className="space-y-6">
          <div className="flex items-center justify-between px-2">
            <h3 className={`text-xs font-bold ${STYLES.textLight} uppercase tracking-[0.2em]`}>Targeted Evidence Cluster</h3>
            <div className={`h-px ${STYLES.border} flex-1 mx-6`} />
            <button
              type="button"
              onClick={handleClearResults}
              disabled={isAnalyzing || !runResponse}
              className="flex items-center gap-2 rounded-full border border-[#E7D7B7] bg-[#FCF8F0] px-3 py-1.5 text-[10px] font-bold uppercase tracking-[0.18em] text-[#8A5A13] transition-all hover:border-[#C96557]/35 hover:text-[#A63D2F] disabled:cursor-not-allowed disabled:opacity-40"
            >
              <Eraser size={12} />
              <span>Clear</span>
            </button>
          </div>

          {runResponse ? (
            <div className={`grid gap-6 ${isAnalyzing ? 'opacity-40 pointer-events-none' : ''} transition-opacity duration-300`}>
              {topEvidence.map((item, index) => (
                <EvidenceCard
                  key={`${currentRunId}:${item.evidenceId}`}
                  item={item}
                  displayRank={index + 1}
                  runId={currentRunId}
                  llmExplainabilityEnabled={debugConfig.llmExplainabilityEnabled}
                />
              ))}
              {topEvidence.length === 0 && !isAnalyzing ? (
                <div className={`p-10 text-center ${STYLES.borderLight} border ${STYLES.radiusCard} ${STYLES.textMuted} font-medium`}>
                  No evidence found for the current clinical profile.
                </div>
              ) : null}
            </div>
          ) : null}

          {topEvidence.length > 0 && (
            <button className={`w-full py-5 border ${STYLES.border} ${STYLES.radiusCard} ${STYLES.textMuted} text-sm font-semibold ${STYLES.surface} ${STYLES.cardHover} transition-all flex items-center justify-center gap-3 group`}>
              Expand Dataset <ArrowRight size={18} className="group-hover:translate-x-1 transition-transform" />
            </button>
          )}
        </div>

        {manualReviewEvidence.length > 0 && (
          <div ref={manualReviewSectionRef} className="space-y-6 scroll-mt-28">
            <div className="flex items-center justify-between px-2">
              <h3 className={`text-xs font-bold ${STYLES.textLight} uppercase tracking-[0.2em]`}>Manual Review Required</h3>
              <div className={`h-px ${STYLES.border} flex-1 mx-6`} />
              <div className="flex items-center gap-2">
                {potentialConflictReviewCount > 0 && (
                  <span className="text-[10px] font-bold text-[#A63D2F] bg-[#FBEAE5] px-3 py-1 rounded-full uppercase border-0">
                    Potential Conflict {potentialConflictReviewCount}
                  </span>
                )}
                <span className="text-[10px] font-bold text-[#8A5A13] bg-[#F6E7C8] px-3 py-1 rounded-full uppercase border-0">
                  Review Queue
                </span>
              </div>
            </div>

            <div className={`p-5 rounded-[28px] border border-[#E7D7B7] bg-[#FCF8F0] text-sm text-[#6B5A45] leading-relaxed ${isAnalyzing ? 'opacity-40 pointer-events-none' : ''} transition-opacity duration-300`}>
              These studies may still matter clinically, but the structured source metadata does not let us confirm the study type with enough confidence. We keep them visible for clinician review and exclude them from the primary ERS ranking. When a matched topic is explicitly do-not-recommend, we surface that separately as a potential conflict rather than claiming a hard conflict verdict.
            </div>

            <div className={`grid gap-6 ${isAnalyzing ? 'opacity-40 pointer-events-none' : ''} transition-opacity duration-300`}>
              {manualReviewEvidence.map((item) => (
                <div key={item.evidenceId}>
                  <ManualReviewCard item={item} />
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Stance Matrix Table */}
        {runResponse ? (
          <div className={isAnalyzing ? 'opacity-50 pointer-events-none transition-opacity' : 'transition-opacity'}>
            <StanceMatrix topEvidence={topEvidence} />
          </div>
        ) : null}
      </div>
    </div>
  );
}
