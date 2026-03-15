"use client";

import React, { useEffect, useState } from 'react';
import { ChevronDown, ExternalLink, CheckCircle2, AlertTriangle, Info, BookOpen, ClipboardCheck } from 'lucide-react';
import { STYLES } from '@/lib/theme';
import { getEvidenceExplainability } from '@/lib/api';
import type { AnalyzeRunResponse, EvidenceExplainability } from '@/lib/contracts';

type EvidenceItem = AnalyzeRunResponse['topEvidence'][0];
type ManualReviewItem = AnalyzeRunResponse['manualReviewEvidence'][0];

export const StatBadge = ({
    icon: Icon,
    label,
    value,
    accentColor,
    valueColor,
    onClick
}: {
    icon: any,
    label: string,
    value: string | number,
    accentColor: string,
    valueColor?: string,
    onClick?: () => void
}) => {
    const Wrapper = onClick ? 'button' : 'div';

    return (
        <Wrapper
            {...(onClick ? { type: 'button', onClick } : {})}
            className={`flex items-center gap-2 px-4 py-2 ${STYLES.radiusChip} ${STYLES.surface} ${STYLES.shadow} ${onClick ? 'transition-transform hover:-translate-y-[1px] cursor-pointer' : ''}`}
        >
            <Icon size={14} className={accentColor} />
            <span className={`text-xs font-semibold uppercase tracking-wider ${STYLES.textMuted}`}>{label}:</span>
            <span className={`text-xs font-bold ${valueColor ?? STYLES.textMain}`}>{value}</span>
        </Wrapper>
    );
};

const ERS_METRIC_COPY: Record<string, { definition: string; meaning: string }> = {
    "Evidence Strength": {
        definition: "How strong the underlying study design and outcome signal are. Randomized trials and rigorous syntheses usually score higher than weaker or less directly actionable evidence.",
        meaning: "Higher means the study is more decision-useful, not just more interesting."
    },
    "Dataset Robustness": {
        definition: "How complete and dependable the structured dataset is for this record. It reflects whether the system has enough clean metadata to classify the study safely.",
        meaning: "Higher means less missing or ambiguous structure, so the ranking is standing on firmer ground."
    },
    "Source Credibility": {
        definition: "How trustworthy the publication source appears in context, based on the journal and the type of evidence channel the study came through.",
        meaning: "Higher means the source is treated as more reliable for clinical triage."
    },
    Recency: {
        definition: "How recent the publication is. Newer studies score higher because the tool prefers evidence that is less likely to be outdated.",
        meaning: "Higher means the evidence is more current, not automatically more correct."
    }
};

const MetricBar = ({
    label,
    value,
    max,
    color,
    help
}: {
    label: string;
    value: number;
    max: number;
    color: string;
    help: { definition: string; meaning: string };
}) => (
    <div
        tabIndex={0}
        aria-label={`${label} explanation`}
        className="group relative space-y-1.5 rounded-[18px] px-2 py-2 outline-none transition-colors hover:bg-[#F7F3EC] focus:bg-[#F7F3EC]"
    >
        <div className={`flex items-center justify-between gap-3 text-[10px] font-bold ${STYLES.textMuted} tracking-wide`}>
            <span>{label.toUpperCase()}</span>
            <span>{value.toFixed(1)}/{max}</span>
        </div>
        <div className={`w-full ${STYLES.bg} h-1.5 rounded-full overflow-hidden`}>
            <div className={`${color} h-full transition-all duration-700`} style={{ width: `${Math.min((value / max) * 100, 100)}%` }}></div>
        </div>
        <div
            role="tooltip"
            className="pointer-events-none absolute left-2 right-2 top-full z-20 mt-2 rounded-[18px] border border-[#E7D7B7] bg-[#FFFDF8] p-3 text-left opacity-0 shadow-[0_18px_38px_rgba(60,42,18,0.14)] transition-all duration-150 group-hover:pointer-events-auto group-hover:opacity-100 group-focus:pointer-events-auto group-focus:opacity-100"
        >
            <div className="text-[11px] font-bold uppercase tracking-[0.16em] text-[#5F584F]">{label}</div>
            <p className="mt-2 text-xs leading-relaxed text-[#2E2E2E]">{help.definition}</p>
            <p className="mt-2 text-[11px] leading-relaxed text-[#6B6B6B]">{help.meaning}</p>
        </div>
    </div>
);

const collapsedTitleStyle: React.CSSProperties = {
    display: '-webkit-box',
    WebkitLineClamp: 3,
    WebkitBoxOrient: 'vertical',
    overflow: 'hidden'
};

const truncateText = (value: string, maxChars: number) => (
    value.length > maxChars ? `${value.slice(0, maxChars).trimEnd()}...` : value
);

const ExplainabilityLoadingState = () => (
    <div className="mb-5 rounded-[22px] border border-[#E7D7B7] bg-[#FFFDF8] p-4">
        <div className="text-[10px] font-bold uppercase tracking-[0.16em] text-[#6B6B6B]">Study Summary</div>
        <div className="mt-3 space-y-2">
            <div className="h-3 w-4/5 animate-pulse rounded-full bg-[#ECE3D2]" />
            <div className="h-3 w-full animate-pulse rounded-full bg-[#ECE3D2]" />
            <div className="h-3 w-3/4 animate-pulse rounded-full bg-[#ECE3D2]" />
        </div>
    </div>
);

export const EvidenceCard = ({
    item,
    displayRank,
    runId,
    llmExplainabilityEnabled
}: {
    item: EvidenceItem;
    displayRank?: number;
    runId: string;
    llmExplainabilityEnabled: boolean;
}) => {
    const [expanded, setExpanded] = useState(false);
    const [evidenceExplainability, setEvidenceExplainability] = useState<EvidenceExplainability | null>(null);
    const [isExplainabilityLoading, setIsExplainabilityLoading] = useState(false);
    const [explainabilityError, setExplainabilityError] = useState<string | null>(null);
    const journalLabel = item.journalTitle ? truncateText(item.journalTitle, 50) : "PubMed source";
    const canLoadExplainability = llmExplainabilityEnabled && item.rank <= 5;

    const statusConfig: Record<string, { colors: string, icon: React.ReactNode, label: string }> = {
        'aligned': { colors: 'text-[#2D5940] bg-[#E8F2EC]', icon: <CheckCircle2 size={16} />, label: 'Aligned' },
        'conflict': { colors: 'text-[#A63D2F] bg-[#FBEAE5]', icon: <AlertTriangle size={16} />, label: 'In Conflict' },
        'guideline_silent': { colors: 'text-[#6B6B6B] bg-[#F0EBE3]', icon: <Info size={16} />, label: 'Guideline-Silent' }
    };

    const status = statusConfig[item.mappingLabel] || statusConfig['guideline_silent'];

    useEffect(() => {
        setEvidenceExplainability(null);
        setExplainabilityError(null);
        setIsExplainabilityLoading(false);
    }, [runId, item.evidenceId]);

    useEffect(() => {
        if (!expanded || !canLoadExplainability || evidenceExplainability || isExplainabilityLoading) {
            return;
        }

        let active = true;

        async function loadExplainability() {
            setIsExplainabilityLoading(true);
            setExplainabilityError(null);
            try {
                const next = await getEvidenceExplainability(runId, item.evidenceId);
                if (active) {
                    setEvidenceExplainability(next);
                }
            } catch (error) {
                if (active) {
                    setExplainabilityError(error instanceof Error ? error.message : "Explainability unavailable.");
                }
            } finally {
                if (active) {
                    setIsExplainabilityLoading(false);
                }
            }
        }

        void loadExplainability();

        return () => {
            active = false;
        };
    }, [canLoadExplainability, expanded, item.evidenceId, runId]);

    return (
        <div className={`${STYLES.radiusCard} ${STYLES.surface} ${STYLES.shadow} ${STYLES.cardHover} border-0 overflow-hidden`}>
            <div className="p-6 flex gap-6 cursor-pointer relative z-10" onClick={() => setExpanded(!expanded)}>
                {/* ERS Score Pillar */}
                <div className={`flex flex-col items-center justify-center w-20 border-r pr-5 ${STYLES.borderLight}`}>
                    <div className={`text-3xl font-black ${STYLES.ersText} leading-none tracking-tight`}>{Math.round(item.ersTotal)}</div>
                    <div className={`text-[10px] font-bold ${STYLES.textLight} mt-1 text-center leading-tight uppercase`}>ERS Score</div>
                    <div className={`w-full ${STYLES.bg} h-1.5 rounded-full mt-4 overflow-hidden`}>
                        <div className={`${STYLES.ersBg} h-full transition-all duration-500`} style={{ width: `${(Math.min(item.ersTotal, 100) / 100) * 100}%` }}></div>
                    </div>
                </div>

                {/* Info Area */}
                <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between gap-3 mb-2">
                        <h3
                            className={`font-bold ${STYLES.textMain} pr-2 ${expanded ? 'text-lg leading-tight' : 'text-base leading-snug'}`}
                            style={expanded ? undefined : collapsedTitleStyle}
                        >
                            {item.title}
                        </h3>
                        <div className={`flex items-center gap-1.5 px-3 py-1.5 ${STYLES.radiusChip} text-[10px] font-bold border-0 whitespace-nowrap uppercase tracking-wide ${status.colors}`}>
                            {status.icon}
                            {status.label}
                        </div>
                    </div>

                    <div className={`flex flex-wrap gap-4 text-[11px] font-bold ${STYLES.textMuted} mb-4 uppercase tracking-wider`}>
                        <span className={`flex items-center gap-1.5 px-3 py-1.5 border ${STYLES.borderLight} ${STYLES.radiusChip}`}>
                            <BookOpen size={14} /> {journalLabel} ({item.publicationYear ?? "2024"})
                        </span>
                    </div>

                    <div className="flex flex-wrap gap-2">
                        {item.mappedTopicTitle && item.mappingLabel !== "guideline_silent" && (
                            <span className={`px-3 py-1 ${STYLES.bg} ${STYLES.textMuted} ${STYLES.radiusChip} text-[10px] font-semibold uppercase tracking-tight`}>
                                Topic: {item.mappedTopicTitle}
                            </span>
                        )}
                        <span className={`px-3 py-1 ${STYLES.bg} ${STYLES.textMuted} ${STYLES.radiusChip} text-[10px] font-semibold uppercase tracking-tight`}>
                            Rank: #{displayRank ?? item.rank}
                        </span>
                    </div>
                </div>

                <button className={`self-center p-3 rounded-full transition-colors ${STYLES.textLight} ${STYLES.hoverBg}`}>
                    <ChevronDown className={`transition-transform duration-[250ms] ease-in-out ${expanded ? 'rotate-180' : ''}`} />
                </button>
            </div>

            {/* Smooth Expand/Collapse Accordion */}
            <div className={`grid transition-all duration-[250ms] ease-in-out ${expanded ? 'grid-rows-[1fr] opacity-100' : 'grid-rows-[0fr] opacity-0'}`}>
                <div className="overflow-hidden">
                    <div className={`px-6 pb-8 pt-2 ${STYLES.bg} border-t ${STYLES.borderLight}`}>
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-10 mt-6">
                            <div className="md:col-span-2 space-y-4">
                                {canLoadExplainability ? (
                                    <>
                                        {isExplainabilityLoading ? <ExplainabilityLoadingState /> : null}
                                        {evidenceExplainability ? (
                                            <>
                                                <div className="mb-5 rounded-[22px] border border-[#E7D7B7] bg-[#FFFDF8] p-4">
                                                    <h4 className={`text-xs font-bold ${STYLES.textMuted} uppercase tracking-widest`}>Why this score?</h4>
                                                    <p className={`mt-3 text-sm ${STYLES.textMain} leading-relaxed opacity-90`}>
                                                        {evidenceExplainability.scoreRationale}
                                                    </p>
                                                </div>

                                                <div className="mb-5 rounded-[22px] border border-[#E7D7B7] bg-[#FFFDF8] p-4">
                                                    <h4 className={`text-xs font-bold ${STYLES.textMuted} uppercase tracking-widest mb-3`}>Study Summary</h4>
                                                    <div className="space-y-3">
                                                        <div>
                                                            <div className="text-[10px] font-bold uppercase tracking-[0.16em] text-[#8A5A13]">Objective</div>
                                                            <p className={`mt-1 text-sm ${STYLES.textMain} leading-relaxed opacity-90`}>
                                                                {evidenceExplainability.studySummary.objective}
                                                            </p>
                                                        </div>
                                                        <div>
                                                            <div className="text-[10px] font-bold uppercase tracking-[0.16em] text-[#8A5A13]">Signal</div>
                                                            <p className={`mt-1 text-sm ${STYLES.textMain} leading-relaxed opacity-90`}>
                                                                {evidenceExplainability.studySummary.signal}
                                                            </p>
                                                        </div>
                                                        <div>
                                                            <div className="text-[10px] font-bold uppercase tracking-[0.16em] text-[#8A5A13]">Takeaway</div>
                                                            <p className={`mt-1 text-sm ${STYLES.textMain} leading-relaxed opacity-90`}>
                                                                {evidenceExplainability.studySummary.takeaway}
                                                            </p>
                                                        </div>
                                                    </div>
                                                </div>

                                                {evidenceExplainability.sourceAnchors.length > 0 ? (
                                                    <div className="mt-5">
                                                        <h4 className={`text-xs font-bold ${STYLES.textMuted} uppercase tracking-widest mb-3`}>Grounding</h4>
                                                        <ul className="space-y-2">
                                                            {evidenceExplainability.sourceAnchors.map((anchor, i) => (
                                                                <li key={`${anchor.sourceId}-${i}`} className={`rounded-[18px] border border-[#E7D7B7] bg-white px-3 py-3 text-xs ${STYLES.textMuted}`}>
                                                                    <div className="flex items-start gap-2">
                                                                        <BookOpen size={12} className="shrink-0 mt-0.5" />
                                                                        <div className="space-y-1">
                                                                            <div className="font-semibold text-[#3C372F]">
                                                                                {anchor.title} ({anchor.year ?? "Unknown year"})
                                                                            </div>
                                                                            <div>{anchor.snippet}</div>
                                                                            <div className="text-[10px] font-bold uppercase tracking-[0.14em] text-[#8A5A13]">
                                                                                {anchor.sourceId}
                                                                            </div>
                                                                        </div>
                                                                    </div>
                                                                </li>
                                                            ))}
                                                        </ul>
                                                    </div>
                                                ) : null}
                                            </>
                                        ) : null}
                                        {explainabilityError ? (
                                            <div className="rounded-[18px] border border-[#E9B7AC] bg-[#FFF5F1] px-4 py-3 text-xs text-[#8B3E2F]">
                                                {explainabilityError}
                                            </div>
                                        ) : null}
                                    </>
                                ) : (
                                    <>
                                        <h4 className={`text-xs font-bold ${STYLES.textMuted} uppercase tracking-widest mb-2`}>Why this label?</h4>
                                        <p className={`text-sm ${STYLES.textMain} leading-relaxed opacity-90 mb-5`}>{item.applicabilityNote}</p>

                                        {item.abstract && (
                                            <div className="mb-5">
                                                <h4 className={`text-xs font-bold ${STYLES.textMuted} uppercase tracking-widest mb-2`}>Abstract</h4>
                                                <p className={`text-sm ${STYLES.textMain} leading-relaxed opacity-90`}>{item.abstract}</p>
                                            </div>
                                        )}

                                        {item.citations.length > 0 && (
                                            <div className="mt-5">
                                                <h4 className={`text-xs font-bold ${STYLES.textMuted} uppercase tracking-widest mb-3`}>Citations</h4>
                                                <ul className="space-y-2">
                                                    {item.citations.map((c, i) => (
                                                        <li key={i} className={`text-xs ${STYLES.textMuted} flex items-start gap-2`}>
                                                            <BookOpen size={12} className="shrink-0 mt-0.5" />
                                                            <span>{c.summary || "Abstract preview not available."} ({c.year})</span>
                                                        </li>
                                                    ))}
                                                </ul>
                                            </div>
                                        )}
                                    </>
                                )}

                                {item.citations?.[0]?.sourceId ? (
                                    <a
                                        href={`https://pubmed.ncbi.nlm.nih.gov/${item.citations[0].sourceId.replace('PMID-', '')}/`}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className={`inline-flex items-center gap-2 text-sm font-bold ${STYLES.primaryText} hover:opacity-70 transition-opacity mt-4`}
                                    >
                                        View Source on PubMed <ExternalLink size={14} />
                                    </a>
                                ) : (
                                    <button className={`flex items-center gap-2 text-sm font-bold ${STYLES.primaryText} hover:opacity-70 transition-opacity mt-4`}>
                                        View Source Details <ExternalLink size={14} />
                                    </button>
                                )}
                            </div>

                            <div className={`${STYLES.surface} p-5 ${STYLES.radiusCard} ${STYLES.shadow}`}>
                                <h4 className={`text-xs font-bold ${STYLES.textMuted} uppercase tracking-widest mb-5`}>ERS Breakdown</h4>
                                <div className="space-y-4">
                                    <MetricBar label="Evidence Strength" value={item.ersBreakdown.evidenceStrength} max={35} color="bg-[#5C7C8A]" help={ERS_METRIC_COPY["Evidence Strength"]} />
                                    <MetricBar label="Dataset Robustness" value={item.ersBreakdown.datasetRobustness} max={25} color="bg-[#8A9A5B]" help={ERS_METRIC_COPY["Dataset Robustness"]} />
                                    <MetricBar label="Source Credibility" value={item.ersBreakdown.sourceCredibility} max={25} color="bg-[#D4A373]" help={ERS_METRIC_COPY["Source Credibility"]} />
                                    <MetricBar label="Recency" value={item.ersBreakdown.recency} max={15} color={STYLES.ersBg} help={ERS_METRIC_COPY.Recency} />
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export const ManualReviewCard = ({ item }: { item: ManualReviewItem }) => {
    const [expanded, setExpanded] = useState(false);
    const journalLabel = item.journalTitle ? truncateText(item.journalTitle, 50) : "PubMed source";

    const mappingConfig: Record<string, { colors: string, icon: React.ReactNode, label: string }> = {
        aligned: { colors: 'text-[#2D5940] bg-[#E8F2EC]', icon: <CheckCircle2 size={16} />, label: 'Aligned Topic Match' },
        conflict: { colors: 'text-[#A63D2F] bg-[#FBEAE5]', icon: <AlertTriangle size={16} />, label: 'Conflict Topic Match' },
        guideline_silent: { colors: 'text-[#6B6B6B] bg-[#F0EBE3]', icon: <Info size={16} />, label: 'No Clear Guideline Match' }
    };

    const mapping = mappingConfig[item.mappingLabel] || mappingConfig.guideline_silent;

    return (
        <div className={`${STYLES.radiusCard} ${STYLES.surface} ${STYLES.shadow} border border-[#E7D7B7] overflow-hidden`}>
            <div className="p-6 flex gap-6 cursor-pointer relative z-10" onClick={() => setExpanded(!expanded)}>
                <div className="flex flex-col items-center justify-center w-20 border-r pr-5 border-[#E7D7B7]">
                    <div className="w-12 h-12 rounded-full bg-[#F6E7C8] text-[#8A5A13] flex items-center justify-center">
                        <ClipboardCheck size={22} />
                    </div>
                    <div className={`text-[10px] font-bold ${STYLES.textLight} mt-3 text-center leading-tight uppercase`}>Manual Review</div>
                </div>

                <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between mb-2 gap-3">
                        <h3
                            className={`font-bold ${STYLES.textMain} pr-2 ${expanded ? 'text-lg leading-tight' : 'text-base leading-snug'}`}
                            style={expanded ? undefined : collapsedTitleStyle}
                        >
                            {item.title}
                        </h3>
                        <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-[10px] font-bold whitespace-nowrap uppercase tracking-wide text-[#8A5A13] bg-[#F6E7C8]">
                            <ClipboardCheck size={16} />
                            Manual Review Required
                        </div>
                    </div>

                    <div className={`flex flex-wrap gap-3 text-[11px] font-bold ${STYLES.textMuted} mb-4 uppercase tracking-wider`}>
                        <span className="flex items-center gap-1.5 px-3 py-1.5 border border-[#E7D7B7] rounded-full">
                            <BookOpen size={14} /> {journalLabel} ({item.publicationYear ?? "Unknown year"})
                        </span>
                        <span className="px-3 py-1.5 rounded-full text-[10px] font-bold uppercase tracking-wide text-[#8A5A13] bg-[#F8F1E4]">
                            Study type not confirmed
                        </span>
                    </div>

                    <div className="flex flex-wrap gap-2">
                        {item.mappedTopicTitle && item.mappingLabel !== "guideline_silent" && (
                            <span className={`px-3 py-1 ${STYLES.bg} ${STYLES.textMuted} ${STYLES.radiusChip} text-[10px] font-semibold uppercase tracking-tight`}>
                                Topic: {item.mappedTopicTitle}
                            </span>
                        )}
                        {item.potentialConflict && (
                            <span className="flex items-center gap-1.5 px-3 py-1 rounded-full text-[10px] font-semibold uppercase tracking-tight text-[#A63D2F] bg-[#FBEAE5]">
                                <AlertTriangle size={14} />
                                Potential Conflict
                            </span>
                        )}
                        <span className={`flex items-center gap-1.5 px-3 py-1 ${mapping.colors} ${STYLES.radiusChip} text-[10px] font-semibold uppercase tracking-tight`}>
                            {mapping.icon}
                            {mapping.label}
                        </span>
                    </div>
                </div>

                <button className={`self-center p-3 rounded-full transition-colors ${STYLES.textLight} ${STYLES.hoverBg}`}>
                    <ChevronDown className={`transition-transform duration-[250ms] ease-in-out ${expanded ? 'rotate-180' : ''}`} />
                </button>
            </div>

            <div className={`grid transition-all duration-[250ms] ease-in-out ${expanded ? 'grid-rows-[1fr] opacity-100' : 'grid-rows-[0fr] opacity-0'}`}>
                <div className="overflow-hidden">
                    <div className={`px-6 pb-8 pt-2 bg-[#FCF8F0] border-t border-[#E7D7B7]`}>
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-10 mt-6">
                            <div className="md:col-span-2 space-y-4">
                                <h4 className={`text-xs font-bold ${STYLES.textMuted} uppercase tracking-widest mb-2`}>Why manual review?</h4>
                                <p className={`text-sm ${STYLES.textMain} leading-relaxed opacity-90 mb-5`}>{item.applicabilityNote}</p>

                                <div className="p-4 rounded-2xl bg-white border border-[#E7D7B7]">
                                    <h4 className={`text-xs font-bold ${STYLES.textMuted} uppercase tracking-widest mb-2`}>How the system treats this item</h4>
                                    <p className={`text-sm ${STYLES.textMain} leading-relaxed opacity-90`}>
                                        This study stays visible for clinician review, but it is excluded from the primary ERS ranking until the evidence type is confirmed.
                                    </p>
                                </div>
                                {item.potentialConflict && (
                                    <div className="p-4 rounded-2xl border border-[#E8B4AA] bg-[#FFF6F3]">
                                        <h4 className="text-xs font-bold uppercase tracking-widest text-[#A63D2F] mb-2">Potential conflict</h4>
                                        <p className={`text-sm ${STYLES.textMain} leading-relaxed opacity-90`}>
                                            The matched guideline topic is currently a do-not-recommend stance, but this record stays in manual review because the study type is still unresolved in the structured source metadata.
                                        </p>
                                    </div>
                                )}

                                {item.citations.length > 0 && (
                                    <div className="mt-5">
                                        <h4 className={`text-xs font-bold ${STYLES.textMuted} uppercase tracking-widest mb-3`}>Citations</h4>
                                        <ul className="space-y-2">
                                            {item.citations.map((c, i) => (
                                                <li key={i} className={`text-xs ${STYLES.textMuted} flex items-start gap-2`}>
                                                    <BookOpen size={12} className="shrink-0 mt-0.5" />
                                                    <span>{c.summary || "Abstract preview not available."} ({c.year})</span>
                                                </li>
                                            ))}
                                        </ul>
                                    </div>
                                )}

                                {item.citations?.[0]?.sourceId ? (
                                    <a
                                        href={`https://pubmed.ncbi.nlm.nih.gov/${item.citations[0].sourceId.replace('PMID-', '')}/`}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className={`inline-flex items-center gap-2 text-sm font-bold ${STYLES.primaryText} hover:opacity-70 transition-opacity mt-4`}
                                    >
                                        View Source on PubMed <ExternalLink size={14} />
                                    </a>
                                ) : null}
                            </div>

                            <div className={`${STYLES.surface} p-5 ${STYLES.radiusCard} ${STYLES.shadow}`}>
                                <h4 className={`text-xs font-bold ${STYLES.textMuted} uppercase tracking-widest mb-5`}>Review Flags</h4>
                                <div className="space-y-3 text-sm">
                                    <div className="p-3 rounded-2xl bg-[#F8F1E4] text-[#8A5A13] font-semibold">
                                        Manual review required
                                    </div>
                                    {item.potentialConflict && (
                                        <div className="p-3 rounded-2xl bg-[#FBEAE5] text-[#A63D2F] font-semibold">
                                            Potential conflict with guideline topic
                                        </div>
                                    )}
                                    <div className={`p-3 rounded-2xl ${STYLES.bg} ${STYLES.textMuted}`}>
                                        Reason: evidence type unspecified
                                    </div>
                                    <div className={`p-3 rounded-2xl ${STYLES.bg} ${STYLES.textMuted}`}>
                                        Rank impact: excluded from scored evidence list
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};
