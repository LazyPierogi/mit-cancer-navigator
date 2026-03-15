"use client";

import { AlertTriangle, CheckCircle2, Info } from 'lucide-react';
import { STYLES } from '@/lib/theme';
import type { AnalyzeRunResponse } from '@/lib/contracts';

type StanceMatrixProps = {
    topEvidence: AnalyzeRunResponse['topEvidence'];
};

export const StanceMatrix = ({ topEvidence }: StanceMatrixProps) => {
    // Group evidence by mappedTopicTitle for the matrix
    const matrixRows = topEvidence.reduce((acc, evidence) => {
        const topic = evidence.mappedTopicTitle || 'General / Unmapped';
        if (!acc[topic]) {
            acc[topic] = {
                topic,
                status: evidence.mappingLabel,
                evidenceCount: 0,
                risk: 'Moderate' // Mocking risk level based on conflict
            };
        }

        acc[topic].evidenceCount += 1;

        // If there's any conflict, escalate status
        if (evidence.mappingLabel === 'conflict') {
            acc[topic].status = 'conflict';
            acc[topic].risk = 'Critical';
        }

        if (acc[topic].status === 'aligned') {
            acc[topic].risk = 'Low (0.0)';
        }

        return acc;
    }, {} as Record<string, any>);

    const rows = Object.values(matrixRows);

    return (
        <section className={`${STYLES.surface} ${STYLES.radiusMain} ${STYLES.shadow} border-0 overflow-hidden`}>
            <div className={`p-8 border-b ${STYLES.border} flex items-center justify-between ${STYLES.bg}`}>
                <div>
                    <h3 className={`text-sm font-bold ${STYLES.textMain} uppercase tracking-wide`}>Guideline Stance Matrix</h3>
                    <p className={`text-[11px] ${STYLES.textLight} font-semibold mt-1 uppercase tracking-widest`}>ESMO 2023 Correlation</p>
                </div>
                <button className={`text-xs font-bold px-5 py-2.5 ${STYLES.surface} border ${STYLES.border} ${STYLES.textMain} ${STYLES.radiusChip} shadow-sm hover:bg-[#F9F8F6] transition-all uppercase tracking-wide`}>
                    Export Mapping
                </button>
            </div>
            <div className="p-0 overflow-x-auto">
                <table className="w-full text-left border-collapse min-w-[600px]">
                    <thead>
                        <tr className={`${STYLES.bg} text-[10px] font-bold ${STYLES.textLight} uppercase tracking-widest`}>
                            <th className="px-8 py-5">Guideline Topic</th>
                            <th className="px-8 py-5">Official Stance</th>
                            <th className="px-8 py-5">Current Evidence</th>
                            <th className="px-8 py-5">Safety Risk</th>
                        </tr>
                    </thead>
                    <tbody className="text-sm">
                        {rows.map((row, idx) => {
                            let stanceUI = null;
                            let riskUI = null;
                            let rowBg = `border-t ${STYLES.borderLight} ${STYLES.hoverBg} transition-colors`;

                            if (row.status === 'aligned') {
                                stanceUI = <span className={`px-3 py-1.5 bg-[#E8F2EC] text-[#2D5940] ${STYLES.radiusChip} text-[10px] font-bold uppercase tracking-wide`}>Recommended</span>;
                                riskUI = <span className={`text-xs font-bold ${STYLES.textLight} uppercase tracking-widest`}>{row.risk}</span>;
                            } else if (row.status === 'conflict') {
                                rowBg = `border-t ${STYLES.borderLight} bg-[#FBEAE5]/30 hover:bg-[#FBEAE5]/50 transition-colors`;
                                stanceUI = <span className={`px-3 py-1.5 bg-[#FBEAE5] text-[#A63D2F] ${STYLES.radiusChip} text-[10px] font-bold uppercase tracking-wide`}>Not Advised</span>;
                                riskUI = <span className="text-xs font-bold text-[#A63D2F] flex items-center gap-2 uppercase tracking-widest"><AlertTriangle size={14} /> {row.risk}</span>;
                            } else {
                                stanceUI = <span className={`px-3 py-1.5 bg-[#F0EBE3] text-[#6B6B6B] ${STYLES.radiusChip} text-[10px] font-bold uppercase tracking-wide`}>Silent / No Data</span>;
                                riskUI = <span className="text-xs font-bold text-[#6B6B6B] uppercase tracking-widest">{row.risk}</span>;
                            }

                            return (
                                <tr key={idx} className={rowBg}>
                                    <td className={`px-8 py-6 font-semibold ${STYLES.textMain}`}>{row.topic}</td>
                                    <td className="px-8 py-6">{stanceUI}</td>
                                    <td className={`px-8 py-6 ${STYLES.textMuted}`}>{row.evidenceCount} Studies</td>
                                    <td className="px-8 py-6">{riskUI}</td>
                                </tr>
                            );
                        })}
                        {rows.length === 0 && (
                            <tr className={`border-t ${STYLES.borderLight} ${STYLES.hoverBg}`}>
                                <td colSpan={4} className={`px-8 py-10 text-center ${STYLES.textMuted} font-medium`}>Provide a clinical profile to view the stance matrix mapped to ESMO guidelines.</td>
                            </tr>
                        )}
                    </tbody>
                </table>
            </div>
        </section>
    );
};
