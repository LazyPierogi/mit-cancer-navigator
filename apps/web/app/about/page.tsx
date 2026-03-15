import { STYLES } from '@/lib/theme';
import { AboutJourneyTimeline } from '@/components/AboutJourneyTimeline';
import {
    Binary,
    BrainCircuit,
    Database,
    FileText,
    FlaskConical,
    GitBranch,
    Rocket,
    ShieldCheck,
    Sparkles,
    Target,
    Telescope,
    UserCheck,
    Workflow
} from 'lucide-react';

const approachCards = [
    {
        title: 'Deterministic scoring',
        description:
            'Evidence is scored against strict parameters like methodology, robustness, recency, and credibility, so ranking remains inspectable instead of vibe-based.',
        icon: Target
    },
    {
        title: 'Guideline mapping',
        description:
            'Retrieved evidence is mapped against curated ESMO topics, making alignment, conflict, and silence visible as explicit labels rather than hidden prompt behavior.',
        icon: FileText
    },
    {
        title: 'Maximum explainability',
        description:
            'The interface shows what was retrieved, why it matched, and where uncertainty remains, so the demo can be audited instead of merely admired.',
        icon: UserCheck
    }
];

const pipelineSteps = [
    {
        step: '01',
        title: 'Normalize the case first',
        description:
            'We turn the patient profile into explicit fields like disease setting, histology, therapy line, and biomarker buckets before any retrieval starts.'
    },
    {
        step: '02',
        title: 'Run deterministic cohort matching',
        description:
            'The rules engine screens out studies that do not fit the actual patient cohort, which keeps obviously off-target papers out of the main path.'
    },
    {
        step: '03',
        title: 'Layer in hybrid retrieval where it helps',
        description:
            'A second engine can use dense embeddings, sparse vectors, and hybrid search to recover relevant evidence when structured metadata is incomplete or too generic.'
    },
    {
        step: '04',
        title: 'Fuse retrieval back into guardrails',
        description:
            'Hybrid candidates are merged back into deterministic ranking and guideline logic, so semantic lift is constrained by explicit safety rails instead of replacing them.'
    },
    {
        step: '05',
        title: 'Escalate uncertainty instead of bluffing',
        description:
            'If a study is ambiguous, weakly typed, or still not patient-fit, it stays visible as uncertainty or manual review instead of being turned into fake confidence.'
    }
];

const stackTiles = [
    {
        title: 'Deterministic engine',
        eyebrow: 'Safety core',
        copy: 'Typed patient schema, deterministic cohort matching, ERS ranking, and guideline labeling remain the source of truth for the clinical-facing result.',
        chips: ['Structured vignette schema', 'ERS scoring', 'Confusion matrix', 'False negatives', 'Guideline mapping', 'Manual review lane'],
        icon: ShieldCheck
    },
    {
        title: 'Hybrid retrieval engine',
        eyebrow: 'Recall engine',
        copy: 'A separate hybrid path can widen candidate recall and semantic topic matching, but it still feeds back into deterministic decision logic instead of bypassing it.',
        chips: ['Dense retrieval', 'Sparse retrieval', 'Hybrid search', 'Semantic rescue'],
        icon: BrainCircuit
    },
    {
        title: 'Qdrant Cloud',
        eyebrow: 'Vector store',
        copy: 'Our external vector backend stores the hybrid retrieval index for chunk-level search across PubMed evidence and ESMO guideline projections.',
        chips: ['Qdrant', 'Cosine', 'Dense field', 'Sparse field', 'Chunk index'],
        icon: Database
    },
    {
        title: 'OpenRouter + text-embedding-3-small',
        eyebrow: 'Embeddings',
        copy: 'The live semantic path uses OpenRouter to generate OpenAI `text-embedding-3-small` vectors. That gives us real embeddings without pretending embeddings are the whole product.',
        chips: ['OpenRouter', 'OpenAI embeddings', 'text-embedding-3-small', '1536-d dense vectors'],
        icon: Binary
    },
    {
        title: 'Hybrid rank fusion',
        eyebrow: 'Retrieval policy',
        copy: 'Dense and sparse results are combined through rank-fusion logic rather than raw-score magic, which makes the merge safer and easier to reason about.',
        chips: ['Dense + sparse', 'RRF', 'Top-K controls', 'Audit-friendly merge'],
        icon: GitBranch
    },
    {
        title: 'Supabase Postgres',
        eyebrow: 'Runtime data',
        copy: 'Imported evidence, guideline topics, semantic metadata, and operational state live in Postgres so the demo runs on tracked runtime data rather than invisible temp files.',
        chips: ['Supabase', 'Postgres', 'Import batches', 'Runtime corpus'],
        icon: FlaskConical
    },
    {
        title: 'Codex + Next.js + FastAPI on Vercel',
        eyebrow: 'App shell',
        copy: 'AI Engeneered with Codex, The interface is a Next.js app and the backend is FastAPI, both deployed on Vercel so the web demo and API stay aligned as one inspectable system.',
        chips: ['GPT-5.4', 'Next.js 15', 'React 19', 'FastAPI', 'Vercel'],
        icon: Rocket
    },
    {
        title: 'Gemini Assistive LLM hooks',
        eyebrow: 'Optional, not authority',
        copy: 'We keep optional import-assist and grounded explainability hooks as explicit toggles, but they are not the decision authority and should never be confused with the core engine.',
        chips: ['Gemini 2.5 Flash', 'Assistive only', 'Grounded summaries', 'No GPT doctor cosplay'],
        icon: Sparkles
    }
];

function SectionHeading({ children }: { children: string }) {
    return <h2 className="border-b border-[#EAE6DF] pb-3 text-xs font-bold uppercase tracking-[0.2em] text-[#C96557]">{children}</h2>;
}

export default function AboutPage() {
    return (
        <div className="mx-auto max-w-5xl space-y-16 py-8">
            <header className="space-y-4 text-center">
                <h1 className="text-4xl font-black tracking-tight text-[#2E2E2E]">MIT Cancer Navigator</h1>
                <p className="mx-auto max-w-2xl text-xl font-medium text-[#6B6B6B]">
                    A transparent evidence engine for NSCLC treatment navigation, designed to show exactly where deterministic safety leads and where hybrid AI can genuinely help.
                </p>
            </header>

            <section className="space-y-6">
                <SectionHeading>The Problem</SectionHeading>
                <p className="text-lg leading-relaxed text-[#2E2E2E]">
                    Current LLM-heavy clinical tools often look impressive right up until you ask what exactly drove the answer. In highly structured oncological settings, hallucinations,
                    non-deterministic outputs, and missing provenance are not cute product quirks. They are trust failures.
                </p>
            </section>

            <section className="space-y-6">
                <SectionHeading>Our Approach</SectionHeading>

                <div className="grid gap-6 md:grid-cols-3">
                    {approachCards.map((card) => {
                        const Icon = card.icon;
                        return (
                            <div key={card.title} className={`${STYLES.surface} ${STYLES.radiusCard} ${STYLES.shadow} border border-[#EAE6DF]/60 p-6`}>
                                <Icon className="mb-4 text-[#C96557]" size={28} />
                                <h3 className="mb-2 font-bold">{card.title}</h3>
                                <p className="text-sm leading-relaxed text-[#6B6B6B]">{card.description}</p>
                            </div>
                        );
                    })}
                </div>
            </section>

            <section className="space-y-8">
                <SectionHeading>How We Use AI</SectionHeading>

                <div className="relative overflow-hidden rounded-[32px] bg-[#201B1A] px-8 py-8 text-white shadow-[0_24px_80px_rgba(32,27,26,0.16)]">
                    <div className="absolute -right-16 -top-12 h-44 w-44 rounded-full bg-[#C96557]/35 blur-3xl" />
                    <div className="absolute bottom-0 left-1/3 h-36 w-36 rounded-full bg-[#E8F2EC]/15 blur-3xl" />
                    <div className="absolute inset-0 opacity-20 [background-image:linear-gradient(to_right,rgba(255,255,255,0.08)_1px,transparent_1px),linear-gradient(to_bottom,rgba(255,255,255,0.08)_1px,transparent_1px)] [background-size:24px_24px]" />

                    <div className="relative space-y-6">
                        <div className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/8 px-4 py-2 text-[10px] font-bold uppercase tracking-[0.28em] text-white/75">
                            <Sparkles size={14} />
                            Transparent AI posture
                        </div>
                        <div className="max-w-4xl space-y-4">
                            <h3 className="text-3xl font-black leading-tight tracking-tight">
                                Deterministic gives us safety and auditability. Hybrid gives us lift, but it does not get to cosplay as magic.
                            </h3>
                            <p className="max-w-3xl text-base leading-relaxed text-white/80">
                                That is the whole point of this demo posture. We want MIT to see where the rules engine is intentionally strict, where hybrid retrieval materially improves recall,
                                and where the limits still are. If the semantic path helps, we show it. If it does not move the decision layer enough, we show that too.
                            </p>
                        </div>

                        <div className="grid gap-4 md:grid-cols-2">
                            <div className="rounded-[24px] border border-white/10 bg-white/7 p-5">
                                <div className="mb-3 flex items-center gap-2 text-[11px] font-bold uppercase tracking-[0.22em] text-white/60">
                                    <ShieldCheck size={14} />
                                    Deterministic runtime
                                </div>
                                <p className="text-sm leading-relaxed text-white/82">
                                    This is the safety rail. Deterministic logic owns cohort matching, ERS ranking, guideline mapping, label assignment, and visible uncertainty handling.
                                </p>
                            </div>
                            <div className="rounded-[24px] border border-white/10 bg-white/7 p-5">
                                <div className="mb-3 flex items-center gap-2 text-[11px] font-bold uppercase tracking-[0.22em] text-white/60">
                                    <BrainCircuit size={14} />
                                    Hybrid semantic lab
                                </div>
                                <p className="text-sm leading-relaxed text-white/82">
                                    This is the lift engine. It uses embeddings, dense plus sparse retrieval, and hybrid search to find better candidates, then hands them back to deterministic guardrails.
                                </p>
                            </div>
                        </div>
                    </div>
                </div>

                <div className="grid gap-6 md:grid-cols-2">
                    <div className="rounded-[28px] border border-[#EAE6DF]/70 bg-white p-6 shadow-[0_18px_40px_rgba(0,0,0,0.05)]">
                        <div className="mb-3 flex items-center gap-2 text-[11px] font-bold uppercase tracking-[0.22em] text-[#6B6B6B]">
                            <Telescope size={14} />
                            Engine one
                        </div>
                        <h3 className="text-2xl font-black tracking-tight text-[#2E2E2E]">Deterministic</h3>
                        <p className="mt-3 text-sm leading-relaxed text-[#6B6B6B]">
                            Built for consistency, traceability, and explainable failure. It is deliberately strict because the safer failure mode in this domain is visible limitation, not smooth improvisation.
                        </p>
                        <div className="mt-4 flex flex-wrap gap-2">
                            {['Safety rail', 'Auditability', 'Repeatable outputs', 'Primary demo authority'].map((item) => (
                                <span key={item} className="rounded-full border border-[#EAE6DF] bg-[#FCFBF8] px-3 py-1.5 text-[11px] font-semibold text-[#2E2E2E]">
                                    {item}
                                </span>
                            ))}
                        </div>
                    </div>

                    <div className="rounded-[28px] border border-[#EAE6DF]/70 bg-white p-6 shadow-[0_18px_40px_rgba(0,0,0,0.05)]">
                        <div className="mb-3 flex items-center gap-2 text-[11px] font-bold uppercase tracking-[0.22em] text-[#6B6B6B]">
                            <GitBranch size={14} />
                            Engine two
                        </div>
                        <h3 className="text-2xl font-black tracking-tight text-[#2E2E2E]">Hybrid + embeddings</h3>
                        <p className="mt-3 text-sm leading-relaxed text-[#6B6B6B]">
                            Built to improve recall when structured metadata is sparse, patient-fit signals are thin, or topic matching needs semantic help. It is valuable exactly because it is bounded.
                        </p>
                        <div className="mt-4 flex flex-wrap gap-2">
                            {['Qdrant hybrid search', 'Dense + sparse vectors', 'Semantic rescue', 'Not a free-form decision maker'].map((item) => (
                                <span key={item} className="rounded-full border border-[#EAE6DF] bg-[#FCFBF8] px-3 py-1.5 text-[11px] font-semibold text-[#2E2E2E]">
                                    {item}
                                </span>
                            ))}
                        </div>
                    </div>
                </div>

                <div className="rounded-[30px] border border-[#EAE6DF]/70 bg-white p-7">
                    <div className="mb-5 flex items-center gap-2 text-[11px] font-bold uppercase tracking-[0.22em] text-[#6B6B6B]">
                        <Workflow size={14} />
                        End-to-end flow
                    </div>
                    <div className="space-y-4">
                        {pipelineSteps.map((step) => (
                            <div key={step.step} className="grid gap-4 rounded-[24px] border border-[#EAE6DF]/70 bg-[#FCFBF8] p-5 md:grid-cols-[72px_1fr] md:items-start">
                                <div className="text-sm font-black uppercase tracking-[0.24em] text-[#C96557]">{step.step}</div>
                                <div>
                                    <h3 className="text-lg font-black text-[#2E2E2E]">{step.title}</h3>
                                    <p className="mt-2 text-sm leading-relaxed text-[#6B6B6B]">{step.description}</p>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                <div className="space-y-4">
                    <div className="flex items-center gap-2 text-[11px] font-bold uppercase tracking-[0.22em] text-[#6B6B6B]">
                        <Binary size={14} />
                        Full stack in plain English
                    </div>
                    <div className="grid gap-5 md:grid-cols-2">
                        {stackTiles.map((tile) => {
                            const Icon = tile.icon;

                            return (
                            <div key={tile.title} className="rounded-[28px] border border-[#EAE6DF]/70 bg-white p-6 shadow-[0_18px_40px_rgba(0,0,0,0.05)]">
                                <div className="flex items-start justify-between gap-4">
                                    <div className="text-[10px] font-bold uppercase tracking-[0.22em] text-[#6B6B6B]">{tile.eyebrow}</div>
                                    <div className="flex h-11 w-11 items-center justify-center rounded-2xl border border-[#EAE6DF] bg-[#FCFBF8] text-[#C96557] shadow-[0_8px_24px_rgba(0,0,0,0.04)]">
                                        <Icon size={18} />
                                    </div>
                                </div>
                                <h3 className="mt-2 text-xl font-black tracking-tight text-[#2E2E2E]">{tile.title}</h3>
                                <p className="mt-3 text-sm leading-relaxed text-[#6B6B6B]">{tile.copy}</p>
                                <div className="mt-4 flex flex-wrap gap-2">
                                    {tile.chips.map((chip) => (
                                        <span key={chip} className="rounded-full border border-[#EAE6DF] bg-[#FCFBF8] px-3 py-1.5 text-[11px] font-semibold text-[#2E2E2E]">
                                            {chip}
                                        </span>
                                    ))}
                                </div>
                            </div>
                            );
                        })}
                    </div>
                </div>

                <div className="rounded-[28px] border border-[#E9B7AC] bg-[#FFF5F1] p-6">
                    <div className="mb-3 flex items-center gap-2 text-[11px] font-bold uppercase tracking-[0.22em] text-[#A63D2F]">
                        <Database size={14} />
                        Demo honesty note
                    </div>
                    <p className="text-sm leading-relaxed text-[#6B6B6B]">
                        We are not presenting a magical all-knowing oncology copilot. We are presenting a transparent system with two engines: one that is deliberately deterministic because trust
                        matters, and one that is deliberately hybrid because retrieval breadth matters. When hybrid improves the result, great. When it only improves candidate recall and not the
                        final label, we say that out loud too.
                    </p>
                </div>

                <AboutJourneyTimeline />
            </section>

            <section className="space-y-6">
                <SectionHeading>Contributors</SectionHeading>
                <p className="text-sm leading-relaxed text-[#6B6B6B]">
                    <strong>MIT AIML - Group 3:</strong><br />
                    BUNDYRA, WIDMER, ESPELAND, LEŚNIEWSKI, RIEKEN, THEIS.<br />
                    <br />
                    Designed to demonstrate how a mission-critical evidence navigator can be honest about both its strengths and its limits.
                </p>
            </section>
        </div>
    );
}
