import { Database, Beaker, Braces } from 'lucide-react';
import { STYLES } from '@/lib/theme';

export default function LabsPage() {
    return (
        <div className="space-y-10 max-w-5xl mx-auto">
            <header className="mb-12 border-b border-[#EAE6DF] pb-6">
                <h1 className="text-3xl font-black text-[#2E2E2E] tracking-tight mb-2">Signal Labs</h1>
                <p className="text-[#6B6B6B] font-medium text-lg">System datasets, vector database, and evaluation tools.</p>
            </header>

            <div className="grid md:grid-cols-2 gap-6">
                {/* Datasets */}
                <div className={`${STYLES.surface} ${STYLES.radiusCard} ${STYLES.shadow} ${STYLES.cardHover} border border-[#EAE6DF]/60 p-8 cursor-pointer`}>
                    <div className={`${STYLES.primaryBg} w-12 h-12 flex items-center justify-center rounded-xl text-white mb-6 shadow-sm`}>
                        <Database size={24} />
                    </div>
                    <h3 className="text-xl font-bold text-[#2E2E2E] mb-3">Curated Datasets</h3>
                    <p className="text-sm text-[#6B6B6B] leading-relaxed mb-6">
                        Access raw PubMed extracts, filtered NSCLC trials, and metadata. Review exclusion criteria and dataset integrity.
                    </p>
                    <div className="flex items-center gap-4 border-t border-[#EAE6DF]/60 pt-5">
                        <span className="text-xs font-bold uppercase tracking-widest text-[#2D5940] bg-[#E8F2EC] px-3 py-1.5 rounded-lg">Aligned</span>
                        <span className="text-xs font-bold uppercase tracking-widest text-[#6B6B6B]">3,412 Resources</span>
                    </div>
                </div>

                {/* Eval Lab */}
                <div className={`${STYLES.surface} ${STYLES.radiusCard} ${STYLES.shadow} ${STYLES.cardHover} border border-[#EAE6DF]/60 p-8 cursor-pointer`}>
                    <div className={`${STYLES.primaryBg} w-12 h-12 flex items-center justify-center rounded-xl text-white mb-6 shadow-sm`}>
                        <Beaker size={24} />
                    </div>
                    <h3 className="text-xl font-bold text-[#2E2E2E] mb-3">Evaluation Lab</h3>
                    <p className="text-sm text-[#6B6B6B] leading-relaxed mb-6">
                        Test and evaluate the deterministic scoring model against the frozen set of 15 golden clinical vignettes.
                    </p>
                    <div className="flex items-center gap-4 border-t border-[#EAE6DF]/60 pt-5">
                        <span className="text-xs font-bold uppercase tracking-widest text-[#C96557]">Run Matrix</span>
                    </div>
                </div>

                {/* Debug Tools */}
                <div className={`${STYLES.surface} ${STYLES.radiusCard} ${STYLES.shadow} ${STYLES.cardHover} border border-[#EAE6DF]/60 p-8 cursor-pointer`}>
                    <div className={`${STYLES.primaryBg} w-12 h-12 flex items-center justify-center rounded-xl text-white mb-6 shadow-sm`}>
                        <Braces size={24} />
                    </div>
                    <h3 className="text-xl font-bold text-[#2E2E2E] mb-3">Vector Embeddings</h3>
                    <p className="text-sm text-[#6B6B6B] leading-relaxed mb-6">
                        Visualize hybrid dense/sparse embeddings in 3D space, troubleshoot clustering logic, and tune RRF boundaries.
                    </p>
                    <div className="flex items-center gap-4 border-t border-[#EAE6DF]/60 pt-5">
                        <span className="text-xs font-bold uppercase tracking-widest text-[#6B6B6B]">Advanced Tools</span>
                    </div>
                </div>
            </div>
        </div>
    );
}
