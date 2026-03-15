'use client';

import { useEffect, useState } from 'react';
import { ShieldCheck, Info, Database, Sparkles, type LucideIcon } from 'lucide-react';
import { STYLES } from '@/lib/theme';
import { getUncertaintyFlagsExplainability } from '@/lib/api';
import type { ImportDebugConfig, UncertaintyFlagsExplainability } from '@/lib/contracts';

type PolicyStripProps = {
  runId: string;
  rulesetVersion: string;
  corpusVersion: string;
  uncertaintyFlags: string[];
  engine: "deterministic" | "semantic_retrieval_lab";
  debugConfig: ImportDebugConfig;
  isSavingDebugConfig: boolean;
  onSemanticRetrievalToggle: () => void;
  onLlmExplainabilityToggle: () => void;
};

function CompactToggle({
  label,
  enabled,
  disabled,
  onToggle,
  icon: Icon
}: {
  label: string;
  enabled: boolean;
  disabled: boolean;
  onToggle: () => void;
  icon: LucideIcon;
}) {
  return (
    <button
      type="button"
      onClick={onToggle}
      disabled={disabled}
      className={`flex items-center gap-3 rounded-2xl border px-3 py-2 transition-all ${
        enabled ? 'border-[#C96557]/35 bg-[#FFF5F1]' : 'border-[#EAE6DF] bg-white'
      } ${disabled ? 'cursor-not-allowed opacity-60' : 'hover:border-[#C96557]/35'}`}
    >
      <div className={`flex h-8 w-8 items-center justify-center rounded-xl ${enabled ? 'bg-[#C96557] text-white' : 'bg-[#F9F8F6] text-[#6B6B6B]'}`}>
        <Icon size={14} />
      </div>
      <div className="text-left">
        <div className="text-[10px] font-bold uppercase tracking-[0.18em] text-[#6B6B6B]">{label}</div>
        <div className={`text-[11px] font-bold uppercase tracking-[0.16em] ${enabled ? 'text-[#A63D2F]' : 'text-[#6B6B6B]'}`}>
          {enabled ? 'On' : 'Off'}
        </div>
      </div>
      <div
        aria-hidden="true"
        className={`relative ml-1 h-7 w-12 rounded-full border transition-all ${
          enabled ? 'border-[#C96557] bg-[#C96557]' : 'border-[#EAE6DF] bg-[#F9F8F6]'
        }`}
      >
        <span
          className={`absolute top-1 h-5 w-5 rounded-full bg-white shadow-[0_6px_18px_rgba(0,0,0,0.12)] transition-all ${
            enabled ? 'left-6' : 'left-1'
          }`}
        />
      </div>
    </button>
  );
}

export function PolicyStrip({
  runId,
  rulesetVersion,
  corpusVersion,
  uncertaintyFlags,
  engine,
  debugConfig,
  isSavingDebugConfig,
  onSemanticRetrievalToggle,
  onLlmExplainabilityToggle
}: PolicyStripProps) {
  const engineLabel = engine === "semantic_retrieval_lab" ? "Semantic Retrieval Lab" : "Deterministic Runtime";
  const tooltipEnabled = debugConfig.llmExplainabilityEnabled;
  const [showUncertaintyTooltip, setShowUncertaintyTooltip] = useState(false);
  const [uncertaintyExplainability, setUncertaintyExplainability] = useState<UncertaintyFlagsExplainability | null>(null);
  const [isUncertaintyExplainabilityLoading, setIsUncertaintyExplainabilityLoading] = useState(false);
  const [uncertaintyExplainabilityError, setUncertaintyExplainabilityError] = useState<string | null>(null);

  useEffect(() => {
    setShowUncertaintyTooltip(false);
    setUncertaintyExplainability(null);
    setIsUncertaintyExplainabilityLoading(false);
    setUncertaintyExplainabilityError(null);
  }, [runId, uncertaintyFlags]);

  useEffect(() => {
    if (!tooltipEnabled) {
      setShowUncertaintyTooltip(false);
      return;
    }
    if (!showUncertaintyTooltip || uncertaintyExplainability || isUncertaintyExplainabilityLoading) {
      return;
    }

    let active = true;

    async function loadExplainability() {
      setIsUncertaintyExplainabilityLoading(true);
      setUncertaintyExplainabilityError(null);
      try {
        const next = await getUncertaintyFlagsExplainability(runId, uncertaintyFlags);
        if (active) {
          setUncertaintyExplainability(next);
        }
      } catch (error) {
        if (active) {
          setUncertaintyExplainabilityError(
            error instanceof Error ? error.message : "Uncertainty flag explainability is unavailable."
          );
        }
      } finally {
        if (active) {
          setIsUncertaintyExplainabilityLoading(false);
        }
      }
    }

    void loadExplainability();

    return () => {
      active = false;
    };
  }, [
    isUncertaintyExplainabilityLoading,
    runId,
    showUncertaintyTooltip,
    tooltipEnabled,
    uncertaintyExplainability,
    uncertaintyFlags
  ]);

  return (
    <div className={`flex flex-col gap-5 rounded-[28px] border ${STYLES.borderLight} bg-[#F9F8F6] px-6 py-5 text-[11px] font-bold uppercase tracking-wider ${STYLES.textMuted}`}>
      <div className="flex flex-col gap-6 xl:flex-row xl:items-start xl:justify-between">
        <div className="min-w-0 xl:flex-1">
          <div className="flex flex-col gap-5">
            <div className="flex items-center gap-2">
              <ShieldCheck size={14} className={STYLES.primaryText} />
              <span>Ruleset:</span>
              <span className={STYLES.textMain}>{rulesetVersion}</span>
            </div>
            <div className="flex items-center gap-2">
              <span>Corpus:</span>
              <span className={STYLES.textMain}>{corpusVersion}</span>
            </div>
            <div className="flex items-center gap-2">
              <span>Scope:</span>
              <span className={STYLES.textMain}>NSCLC treatment evidence only</span>
            </div>
            <div className="flex flex-wrap items-center gap-3 pt-1">
              <div
                className="relative"
                onMouseEnter={tooltipEnabled ? () => setShowUncertaintyTooltip(true) : undefined}
                onMouseLeave={tooltipEnabled ? () => setShowUncertaintyTooltip(false) : undefined}
              >
                <div
                  role={tooltipEnabled ? "button" : undefined}
                  tabIndex={tooltipEnabled ? 0 : -1}
                  onFocus={tooltipEnabled ? () => setShowUncertaintyTooltip(true) : undefined}
                  onBlur={tooltipEnabled ? () => setShowUncertaintyTooltip(false) : undefined}
                  className={`flex items-center gap-2 rounded-[18px] px-2 py-1 text-amber-600 transition-colors ${
                    tooltipEnabled ? 'cursor-help hover:bg-[#FFF4DF] focus:bg-[#FFF4DF] outline-none' : ''
                  }`}
                >
                  <Info size={14} />
                  <span>Uncertainty Flags:</span>
                  <span className="text-amber-700">{uncertaintyFlags.length}</span>
                </div>

                {tooltipEnabled && showUncertaintyTooltip ? (
                  <div
                    role="tooltip"
                    className="absolute left-0 top-full z-30 mt-3 w-[min(44rem,calc(100vw-4rem))] rounded-[26px] border border-[#E7D7B7] bg-[#FFFDF8] p-5 normal-case shadow-[0_24px_60px_rgba(60,42,18,0.18)]"
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div>
                        <div className="text-[11px] font-bold uppercase tracking-[0.18em] text-[#8A5A13]">
                          Uncertainty Flags
                        </div>
                        <p className="mt-2 text-sm font-semibold leading-relaxed text-[#2E2E2E]">
                          {isUncertaintyExplainabilityLoading
                            ? "Building an operator-facing explanation for why these flags are present in this run..."
                            : uncertaintyExplainability?.summary}
                        </p>
                      </div>
                      <div className="rounded-full bg-[#F7E8CC] px-3 py-1 text-[10px] font-bold uppercase tracking-[0.16em] text-[#8A5A13]">
                        {isUncertaintyExplainabilityLoading
                          ? "Loading"
                          : uncertaintyExplainability?.providerStatus === "llm_grounded"
                            ? "LLM"
                            : "Local"}
                      </div>
                    </div>

                    {uncertaintyExplainabilityError ? (
                      <p className="mt-4 text-sm leading-relaxed text-[#A63D2F]">{uncertaintyExplainabilityError}</p>
                    ) : null}

                    {!isUncertaintyExplainabilityLoading && uncertaintyExplainability ? (
                      <>
                        <div className="mt-4 grid gap-4 md:grid-cols-2">
                          <div className="rounded-[20px] border border-[#EFE4CF] bg-white/70 p-4">
                            <div className="text-[10px] font-bold uppercase tracking-[0.16em] text-[#5F584F]">Why They Exist</div>
                            <p className="mt-2 text-sm leading-relaxed text-[#2E2E2E]">
                              {uncertaintyExplainability.whyFlagsExist}
                            </p>
                          </div>
                          <div className="rounded-[20px] border border-[#EFE4CF] bg-white/70 p-4">
                            <div className="text-[10px] font-bold uppercase tracking-[0.16em] text-[#5F584F]">What It Means</div>
                            <p className="mt-2 text-sm leading-relaxed text-[#2E2E2E]">
                              {uncertaintyExplainability.whatItMeans}
                            </p>
                          </div>
                        </div>

                        {uncertaintyExplainability.flags.length > 0 ? (
                          <div className="mt-4">
                            <div className="text-[10px] font-bold uppercase tracking-[0.16em] text-[#5F584F]">Current Run Flags</div>
                            <div className="mt-2 flex flex-wrap gap-2">
                              {uncertaintyExplainability.flags.map((flag) => (
                                <span
                                  key={flag}
                                  className="rounded-full border border-[#E7D7B7] bg-[#FFF7EA] px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.08em] text-[#8A5A13]"
                                >
                                  {flag.replace(":", " · ")}
                                </span>
                              ))}
                            </div>
                          </div>
                        ) : null}
                      </>
                    ) : null}
                  </div>
                ) : null}
              </div>
              <div className={`flex items-center gap-2 px-3 py-1.5 ${STYLES.radiusChip} bg-[#E8F2EC] text-[#2D5940]`}>
                <Database size={14} />
                <span className="text-[11px] font-bold uppercase tracking-wider">Engine: {engineLabel}</span>
              </div>
            </div>
          </div>
        </div>

        <div className="flex justify-start xl:justify-end">
          <div className="flex flex-col gap-3">
            <CompactToggle
              label="Semantic Retrieval"
              enabled={debugConfig.semanticRetrievalEnabled}
              disabled={isSavingDebugConfig}
              onToggle={onSemanticRetrievalToggle}
              icon={Database}
            />
            <CompactToggle
              label="LLM Explainability"
              enabled={debugConfig.llmExplainabilityEnabled}
              disabled={isSavingDebugConfig}
              onToggle={onLlmExplainabilityToggle}
              icon={Sparkles}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
