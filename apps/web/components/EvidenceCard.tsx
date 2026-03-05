"use client";

import React, { useState } from 'react';
import { ChevronDown, ExternalLink, CheckCircle2, AlertTriangle, Info, BookOpen, Clock } from 'lucide-react';
import { STYLES } from '@/lib/theme';
import type { AnalyzeRunResponse } from '@/lib/contracts';

type EvidenceItem = AnalyzeRunResponse['topEvidence'][0];

export const StatBadge = ({ icon: Icon, label, value, accentColor }: { icon: any, label: string, value: string | number, accentColor: string }) => (
    <div className={`flex items-center gap-2 px-4 py-2 ${STYLES.radiusChip} ${STYLES.surface} ${STYLES.shadow}`}>
        <Icon size={14} className={accentColor} />
        <span className={`text-xs font-semibold uppercase tracking-wider ${STYLES.textMuted}`}>{label}:</span>
        <span className={`text-xs font-bold ${STYLES.textMain}`}>{value}</span>
    </div>
);

const MetricBar = ({ label, value, max, color }: { label: string, value: number, max: number, color: string }) => (
    <div className="space-y-1.5">
        <div className={`flex justify-between text-[10px] font-bold ${STYLES.textMuted} tracking-wide`}>
            <span>{label.toUpperCase()}</span>
            <span>{value.toFixed(1)}/{max}</span>
        </div>
        <div className={`w-full ${STYLES.bg} h-1.5 rounded-full overflow-hidden`}>
            <div className={`${color} h-full transition-all duration-700`} style={{ width: `${Math.min((value / max) * 100, 100)}%` }}></div>
        </div>
    </div>
);

export const EvidenceCard = ({ item }: { item: EvidenceItem }) => {
    const [expanded, setExpanded] = useState(false);

    const statusConfig: Record<string, { colors: string, icon: React.ReactNode, label: string }> = {
        'aligned': { colors: 'text-[#2D5940] bg-[#E8F2EC]', icon: <CheckCircle2 size={16} />, label: 'Aligned' },
        'conflict': { colors: 'text-[#A63D2F] bg-[#FBEAE5]', icon: <AlertTriangle size={16} />, label: 'In Conflict' },
        'guideline_silent': { colors: 'text-[#6B6B6B] bg-[#F0EBE3]', icon: <Info size={16} />, label: 'Guideline-Silent' }
    };

    const status = statusConfig[item.mappingLabel] || statusConfig['guideline_silent'];

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
                <div className="flex-1">
                    <div className="flex items-start justify-between mb-2">
                        <h3 className={`text-lg font-bold ${STYLES.textMain} leading-tight pr-4`}>{item.title}</h3>
                        <div className={`flex items-center gap-1.5 px-3 py-1.5 ${STYLES.radiusChip} text-[10px] font-bold border-0 whitespace-nowrap uppercase tracking-wide ${status.colors}`}>
                            {status.icon}
                            {status.label}
                        </div>
                    </div>

                    <div className={`flex flex-wrap gap-4 text-[11px] font-bold ${STYLES.textMuted} mb-4 uppercase tracking-wider`}>
                        <span className={`flex items-center gap-1.5 px-3 py-1.5 border ${STYLES.borderLight} ${STYLES.radiusChip}`}>
                            <BookOpen size={14} /> {item.citations?.[0]?.sourceId?.replace('PMID-', 'JCO ') || "JCO"} ({item.publicationYear ?? "2024"})
                        </span>
                    </div>

                    <div className="flex flex-wrap gap-2">
                        {item.mappedTopicTitle && (
                            <span className={`px-3 py-1 ${STYLES.bg} ${STYLES.textMuted} ${STYLES.radiusChip} text-[10px] font-semibold uppercase tracking-tight`}>
                                Topic: {item.mappedTopicTitle}
                            </span>
                        )}
                        <span className={`px-3 py-1 ${STYLES.bg} ${STYLES.textMuted} ${STYLES.radiusChip} text-[10px] font-semibold uppercase tracking-tight`}>
                            Rank: #{item.rank}
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
                                                    <span>{c.title} ({c.year})</span>
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
                                ) : (
                                    <button className={`flex items-center gap-2 text-sm font-bold ${STYLES.primaryText} hover:opacity-70 transition-opacity mt-4`}>
                                        View Source Details <ExternalLink size={14} />
                                    </button>
                                )}
                            </div>

                            <div className={`${STYLES.surface} p-5 ${STYLES.radiusCard} ${STYLES.shadow}`}>
                                <h4 className={`text-xs font-bold ${STYLES.textMuted} uppercase tracking-widest mb-5`}>ERS Breakdown</h4>
                                <div className="space-y-4">
                                    <MetricBar label="Evidence Strength" value={item.ersBreakdown.evidenceStrength} max={40} color="bg-[#5C7C8A]" />
                                    <MetricBar label="Dataset Robustness" value={item.ersBreakdown.datasetRobustness} max={30} color="bg-[#8A9A5B]" />
                                    <MetricBar label="Source Credibility" value={item.ersBreakdown.sourceCredibility} max={20} color="bg-[#D4A373]" />
                                    <MetricBar label="Recency" value={item.ersBreakdown.recency} max={10} color={STYLES.ersBg} />
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};
