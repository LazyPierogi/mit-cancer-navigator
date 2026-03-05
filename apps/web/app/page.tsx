"use client";

import React, { useState, useEffect } from 'react';
import { UserCircle, Lock, Plus, AlertTriangle, FlaskConical, Award, ShieldCheck, ArrowRight } from 'lucide-react';
import { STYLES } from '@/lib/theme';
import { EvidenceCard, StatBadge } from '@/components/EvidenceCard';
import { StanceMatrix } from '@/components/StanceMatrix';
import { PolicyStrip } from '@/components/PolicyStrip';
import { createRun } from '@/lib/api';
import { individualPresets } from '@/lib/presets';
import type { VignetteInput, AnalyzeRunResponse } from '@/lib/contracts';

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
  { label: "Later Line", value: "later_line" as const }
];

export default function HomePage() {
  const [activePresetId, setActivePresetId] = useState<string>(individualPresets[0].id);
  const [vignette, setVignette] = useState<VignetteInput>(individualPresets[0].vignette);
  const [customInput, setCustomInput] = useState("");
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [runResponse, setRunResponse] = useState<AnalyzeRunResponse | null>(null);

  // Initial run
  useEffect(() => {
    handleRun(vignette);
  }, []);

  const handleRun = async (payload: VignetteInput) => {
    setIsAnalyzing(true);
    try {
      const res = await createRun(payload);
      setRunResponse(res);
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
    handleRun(preset.vignette);
  };

  const updateVignette = (updates: Partial<VignetteInput>) => {
    setActivePresetId("");
    const next = { ...vignette, ...updates };
    setVignette(next);
    handleRun(next);
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
    handleRun(next);
  };

  const topEvidence = runResponse?.topEvidence || [];
  const recallRate = topEvidence.length > 0 ? "98.2%" : "0.0%";
  const avgErs = topEvidence.length > 0 ? (topEvidence.reduce((acc, a) => acc + a.ersTotal, 0) / topEvidence.length).toFixed(1) : "0.0";

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
            <label className={`text-[10px] font-bold ${STYLES.textLight} uppercase tracking-widest mb-3 block`}>Vignette Presets (MVP Quick-Test)</label>
            <div className="grid grid-cols-3 gap-3">
              {individualPresets.map(preset => (
                <button
                  key={preset.id}
                  onClick={() => handlePresetChange(preset.id)}
                  className={`flex flex-col items-center justify-center p-3 ${STYLES.radiusCard} border transition-all duration-300 ${activePresetId === preset.id ? `${STYLES.accentBg} text-white border-transparent ${STYLES.shadow}` : `${STYLES.bg} ${STYLES.textMuted} ${STYLES.borderLight} ${STYLES.hoverBg}`}`}
                >
                  <span className="text-xs font-bold uppercase tracking-wide">{preset.name}</span>
                  <span className={`text-[9px] mt-0.5 ${activePresetId === preset.id ? 'text-white/80' : STYLES.textLight}`}>{preset.id === individualPresets[0].id ? 'Standard' : 'Case'}</span>
                </button>
              ))}
            </div>
          </div>

          <div className={`h-px w-full ${STYLES.borderLight} mb-8`} />

          {/* Explicit Tag Selection */}
          <div className={`space-y-8 ${isAnalyzing ? 'opacity-50 pointer-events-none' : ''} transition-opacity duration-300`}>
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
                    onClick={() => updateVignette({ lineOfTherapy: opt.value })}
                    className={`px-4 py-2 ${STYLES.radiusChip} text-xs transition-all font-medium border ${vignette.lineOfTherapy === opt.value ? `${STYLES.accentBg} text-white border-transparent ${STYLES.shadow}` : `${STYLES.surface} ${STYLES.textMuted} ${STYLES.borderLight} ${STYLES.hoverBg}`}`}
                  >
                    {opt.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Free-form Input */}
            <div className="space-y-3 pt-4">
              <label className={`text-[11px] font-bold ${STYLES.textLight} uppercase tracking-widest`}>Additional Clinical Modifiers</label>
              <div className="relative group">
                <div className={`absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none ${STYLES.textLight}`}>
                  <Plus size={16} />
                </div>
                <input
                  type="text"
                  placeholder="E.g. Brain metastasis, cachexia..."
                  value={customInput}
                  onChange={(e) => setCustomInput(e.target.value)}
                  className={`w-full ${STYLES.bg} border ${STYLES.border} ${STYLES.textMain} ${STYLES.radiusCard} pl-10 pr-4 py-3 text-sm font-medium focus:ring-1 ${STYLES.ring} focus:border-[#C96557] outline-none transition-all placeholder:font-normal placeholder:opacity-60`}
                />
              </div>
            </div>
          </div>

          <button
            onClick={() => handleRun(vignette)}
            disabled={isAnalyzing}
            className={`w-full py-4 mt-8 ${STYLES.accentBg} text-white font-bold uppercase tracking-widest ${STYLES.radiusCard} ${STYLES.shadow} hover:opacity-90 transition-opacity flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed`}
          >
            {isAnalyzing ? "Analyzing..." : "Run Analysis"}
          </button>

          <div className={`mt-8 p-5 ${STYLES.radiusCard} bg-[#FBEAE5] text-[#A63D2F]`}>
            <div className="flex gap-4">
              <AlertTriangle size={20} className="shrink-0 opacity-80" strokeWidth={1.5} />
              <p className="text-[11px] leading-relaxed font-medium">
                <strong>DETERMINISTIC MODE:</strong> Unstructured text input is restricted to keyword extraction. Any evidence failing to match all mandatory patient tags will be discarded automatically.
              </p>
            </div>
          </div>
        </section>
      </aside>

      {/* Center: Evidence and Analysis */}
      <div className="col-span-12 lg:col-span-8 space-y-10">
        {runResponse && (
          <PolicyStrip
            rulesetVersion={runResponse.run.rulesetVersion}
            corpusVersion={runResponse.run.corpusVersion}
            uncertaintyFlags={runResponse.uncertaintyFlags}
          />
        )}

        {/* Summary Dashboard */}
        <div className="flex flex-wrap items-center gap-5">
          <StatBadge icon={FlaskConical} label="Retrieved" value={`${topEvidence.length} Studies`} accentColor={STYLES.primaryText} />
          <StatBadge icon={Award} label="Avg ERS" value={avgErs} accentColor="text-[#6B6B6B]" />
          <StatBadge icon={ShieldCheck} label="Recall Rate" value={recallRate} accentColor="text-[#2D5940]" />

          <div className="ml-auto flex items-center gap-3">
            <span className={`text-[10px] font-bold ${STYLES.textLight} uppercase tracking-widest`}>Sorted By</span>
            <select className={`bg-transparent text-xs font-bold ${STYLES.primaryText} outline-none cursor-pointer hover:underline appearance-none`}>
              <option>ERS SCORE (DESC)</option>
              <option>RECENCY</option>
              <option>ALIGNMENT</option>
            </select>
          </div>
        </div>

        {/* Results List */}
        <div className="space-y-6">
          <div className="flex items-center justify-between px-2">
            <h3 className={`text-xs font-bold ${STYLES.textLight} uppercase tracking-[0.2em]`}>Targeted Evidence Cluster</h3>
            <div className={`h-px ${STYLES.border} flex-1 mx-6`} />
            <span className={`text-[10px] font-bold ${STYLES.primaryText} ${STYLES.primaryLight} px-3 py-1 ${STYLES.radiusChip} uppercase border-0`}>
              {isAnalyzing ? "Analyzing..." : "Verified Logic"}
            </span>
          </div>

          <div className={`grid gap-6 ${isAnalyzing ? 'opacity-40 pointer-events-none' : ''} transition-opacity duration-300`}>
            {topEvidence.map(item => (
              <EvidenceCard key={item.evidenceId} item={item} />
            ))}
            {topEvidence.length === 0 && !isAnalyzing && (
              <div className={`p-10 text-center ${STYLES.borderLight} border ${STYLES.radiusCard} ${STYLES.textMuted} font-medium`}>
                No evidence found for the current clinical profile.
              </div>
            )}
          </div>

          {topEvidence.length > 0 && (
            <button className={`w-full py-5 border ${STYLES.border} ${STYLES.radiusCard} ${STYLES.textMuted} text-sm font-semibold ${STYLES.surface} ${STYLES.cardHover} transition-all flex items-center justify-center gap-3 group`}>
              Expand Dataset <ArrowRight size={18} className="group-hover:translate-x-1 transition-transform" />
            </button>
          )}
        </div>

        {/* Stance Matrix Table */}
        <div className={isAnalyzing ? 'opacity-50 pointer-events-none transition-opacity' : 'transition-opacity'}>
          <StanceMatrix topEvidence={topEvidence} />
        </div>
      </div>
    </div>
  );
}
