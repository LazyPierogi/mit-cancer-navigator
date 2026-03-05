import { STYLES } from '@/lib/theme';
import { Target, FileText, UserCheck } from 'lucide-react';

export default function AboutPage() {
    return (
        <div className="max-w-4xl mx-auto space-y-16 py-8">
            <header className="text-center space-y-4">
                <h1 className="text-4xl font-black text-[#2E2E2E] tracking-tight">MIT Cancer Navigator</h1>
                <p className="text-xl text-[#6B6B6B] font-medium max-w-2xl mx-auto">
                    A deterministic evidence search engine engineered for precision, explainability, and total clinical transparency.
                </p>
            </header>

            <section className="space-y-6">
                <h2 className="text-xs font-bold uppercase tracking-[0.2em] text-[#C96557] border-b border-[#EAE6DF] pb-3">The Problem</h2>
                <p className="text-lg leading-relaxed text-[#2E2E2E]">
                    Current LLM-based clinical decision tools suffer from non-deterministic generation, hallucinations, and lack of verifiable provenance. In highly structured oncological settings, probabilistic answers introduce unacceptable risks.
                </p>
            </section>

            <section className="space-y-6">
                <h2 className="text-xs font-bold uppercase tracking-[0.2em] text-[#C96557] border-b border-[#EAE6DF] pb-3">Our Approach</h2>

                <div className="grid md:grid-cols-3 gap-6">
                    <div className={`${STYLES.surface} p-6 ${STYLES.radiusCard} ${STYLES.shadow} border border-[#EAE6DF]/60`}>
                        <Target className="text-[#C96557] mb-4" size={28} />
                        <h3 className="font-bold mb-2">Deterministic Scoring</h3>
                        <p className="text-sm text-[#6B6B6B] leading-relaxed">
                            Evidence is scored against strict parameters (Methodology, Robustness, Recency, Credibility) yielding a verifiable ERS.
                        </p>
                    </div>

                    <div className={`${STYLES.surface} p-6 ${STYLES.radiusCard} ${STYLES.shadow} border border-[#EAE6DF]/60`}>
                        <FileText className="text-[#C96557] mb-4" size={28} />
                        <h3 className="font-bold mb-2">Alignment Labeling</h3>
                        <p className="text-sm text-[#6B6B6B] leading-relaxed">
                            Retrieved chunks are actively mapped against official guidelines (e.g. ESMO 2023) yielding explicit 'Aligned' or 'Conflict' tags.
                        </p>
                    </div>

                    <div className={`${STYLES.surface} p-6 ${STYLES.radiusCard} ${STYLES.shadow} border border-[#EAE6DF]/60`}>
                        <UserCheck className="text-[#C96557] mb-4" size={28} />
                        <h3 className="font-bold mb-2">Maximum Explainability</h3>
                        <p className="text-sm text-[#6B6B6B] leading-relaxed">
                            Instead of chat blobs, physicians receive transparent interfaces showing exactly what evidence supported the outcome and why it is ranked.
                        </p>
                    </div>
                </div>
            </section>

            <section className="space-y-6">
                <h2 className="text-xs font-bold uppercase tracking-[0.2em] text-[#C96557] border-b border-[#EAE6DF] pb-3">Contributors</h2>
                <p className="text-[#6B6B6B] leading-relaxed text-sm">
                    <strong>MIT AIML - Group 3:</strong><br />
                    BUNDYRA, WIDMER, ESPELAND, LEŚNIEWSKI, RIEKEN, THEIS.<br /><br />
                    Designed to demonstrate how structured RAG systems should be built for mission-critical, high-compliance environments.
                </p>
            </section>
        </div>
    );
}
