"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import {
  Binary,
  BrainCircuit,
  Database,
  FileCheck,
  FlaskConical,
  Rocket,
  ShieldCheck,
  Sparkles,
  Target,
  Workflow,
  type LucideIcon
} from "lucide-react";

type JourneyStep = {
  phase: string;
  title: string;
  description: string;
  detail: string;
  chips: string[];
  icon: LucideIcon;
};

const journeySteps: JourneyStep[] = [
  {
    phase: "Phase 01",
    title: "Deterministic Python core",
    description: "We started with a rules-first engine and validation harness in Python before any fancy semantic layer entered the room.",
    detail: "The first real product move was not chat. It was deterministic validation, typed rules, and a safety-oriented core that could be audited study by study.",
    chips: ["Python rules", "Validation harness", "Safety-first", "Auditability"],
    icon: ShieldCheck
  },
  {
    phase: "Phase 02",
    title: "Tiny evaluation packs",
    description: "The early system was exercised on a tiny but controllable set of patient vignettes plus starter ESMO and PubMed evidence packs.",
    detail: "This gave us a sane sandbox: roughly 10 to 15 patient vignettes and a tiny bundle of papers and guideline examples, small enough to inspect manually and break on purpose.",
    chips: ["Seed vignettes", "Starter PubMed", "Starter ESMO", "Manual inspection"],
    icon: FlaskConical
  },
  {
    phase: "Phase 03",
    title: "Data sanitation and structuring",
    description: "We then focused on cleaning the data so patient cases, PubMed rows, and ESMO topics could stop talking past each other.",
    detail: "That meant normalizing fields, enforcing shaped records, and treating missing metadata as an explicit problem rather than a silent shrug.",
    chips: ["Normalization", "Structured fields", "Sanitation", "Canonical shapes"],
    icon: Database
  },
  {
    phase: "Phase 04",
    title: "Shared clinical vocabulary",
    description: "The next leap was translation between adjacent dialects: vignette language, ESMO tags, and PubMed intervention wording.",
    detail: "This is where we learned that a deterministic system can still fail for semantic reasons when tags like `egfr-tki`, `tki`, and `targeted` mean the same thing to humans but not to machines.",
    chips: ["Ontology alignment", "Histology mapping", "Tag translation", "Cross-source semantics"],
    icon: Workflow
  },
  {
    phase: "Phase 05",
    title: "Next.js + FastAPI on Vercel",
    description: "Once the contracts stabilized, we gave the project a real web face and an online API instead of keeping it as a nice local science experiment.",
    detail: "This is where the demo became a product surface: Next.js on the front, FastAPI behind it, both deployed on Vercel so the flow could be exercised live.",
    chips: ["Next.js", "FastAPI", "Vercel", "Live demo surface"],
    icon: Rocket
  },
  {
    phase: "Phase 06",
    title: "Deterministic runtime online",
    description: "With the app live, the deterministic engine became the visible authority for cohort matching, ERS ranking, and guideline labeling.",
    detail: "This phase matters because it locked in the central promise: the online demo should be inspectable, repeatable, and willing to show uncertainty instead of bluffing.",
    chips: ["ERS", "Cohort matching", "Guideline labels", "Manual review"],
    icon: Target
  },
  {
    phase: "Phase 07",
    title: "Hybrid retrieval and vector infra",
    description: "Only after the deterministic base was credible did we add Supabase runtime persistence, hybrid retrieval, Qdrant, and OpenRouter embeddings.",
    detail: "The semantic path grew in stages: semantic chunk storage, external vector search, dense plus sparse retrieval, rank fusion, and rescue back into deterministic decision logic.",
    chips: ["Supabase Postgres", "Qdrant", "OpenRouter", "Hybrid search"],
    icon: BrainCircuit
  },
  {
    phase: "Phase 08",
    title: "Assistive LLM hooks",
    description: "The last layer is assistive and explicitly non-authoritative: grounded summaries and import help, never the clinical source of truth.",
    detail: "This keeps the story honest. We can use an assistive LLM layer where it adds ergonomics, but it does not get to impersonate the deterministic engine or rewrite the evidence contract.",
    chips: ["Gemini assistive hooks", "Grounded summaries", "Optional layer", "Not decision authority"],
    icon: Sparkles
  }
];

function clamp(value: number, min: number, max: number) {
  return Math.min(Math.max(value, min), max);
}

export function AboutJourneyTimeline() {
  const sectionRef = useRef<HTMLDivElement | null>(null);
  const stickyPanelRef = useRef<HTMLDivElement | null>(null);
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    let frame = 0;

    function updateProgress() {
      const section = sectionRef.current;
      const stickyPanel = stickyPanelRef.current;
      if (!section || !stickyPanel) {
        return;
      }

      const rect = section.getBoundingClientRect();
      const stickyHeight = stickyPanel.getBoundingClientRect().height;
      const stickyTopOffset = 96;
      const lockedDistance = stickyTopOffset - rect.top;
      const scrollableDistance = section.offsetHeight - stickyHeight - stickyTopOffset;
      const next = clamp(lockedDistance / Math.max(scrollableDistance, 1), 0, 1);
      setProgress(next);
    }

    function scheduleUpdate() {
      cancelAnimationFrame(frame);
      frame = window.requestAnimationFrame(updateProgress);
    }

    updateProgress();
    window.addEventListener("scroll", scheduleUpdate, { passive: true });
    window.addEventListener("resize", scheduleUpdate);

    return () => {
      cancelAnimationFrame(frame);
      window.removeEventListener("scroll", scheduleUpdate);
      window.removeEventListener("resize", scheduleUpdate);
    };
  }, []);

  const activeIndex = useMemo(() => {
    return journeySteps.reduce((currentIndex, _step, index) => {
      const threshold = index / Math.max(journeySteps.length - 1, 1);
      return progress >= threshold ? index : currentIndex;
    }, 0);
  }, [progress]);

  const activeStep = journeySteps[activeIndex] ?? journeySteps[0];

  return (
    <section className="space-y-6">
      <div className="flex items-center gap-2 text-[11px] font-bold uppercase tracking-[0.22em] text-[#6B6B6B]">
        <Binary size={14} />
        Build journey
      </div>

      <p className="max-w-3xl text-sm leading-relaxed text-[#6B6B6B]">
        This is the honest build order. We did not begin with a magic copilot. We began with deterministic rules, tiny test packs, structured cleanup, and only later earned the right to add hybrid retrieval and assistive layers.
      </p>

      <div ref={sectionRef} className="relative hidden md:block md:h-[210vh]">
        <div ref={stickyPanelRef} className="sticky top-24">
          <div className="overflow-hidden rounded-[32px] border border-[#EAE6DF]/70 bg-[#201B1A] p-8 text-white shadow-[0_24px_80px_rgba(32,27,26,0.14)]">
            <div className="absolute inset-0 opacity-15 [background-image:linear-gradient(to_right,rgba(255,255,255,0.08)_1px,transparent_1px),linear-gradient(to_bottom,rgba(255,255,255,0.08)_1px,transparent_1px)] [background-size:24px_24px]" />
            <div className="relative">
              <div className="grid gap-6 lg:grid-cols-[1.15fr_0.85fr]">
                <div className="space-y-4">
                  <div className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/8 px-4 py-2 text-[10px] font-bold uppercase tracking-[0.28em] text-white/72">
                    <Workflow size={14} />
                    Scroll to advance
                  </div>
                  <div>
                    <div className="text-[11px] font-bold uppercase tracking-[0.22em] text-white/48">{activeStep.phase}</div>
                    <h3 className="mt-3 text-3xl font-black tracking-tight text-white">{activeStep.title}</h3>
                    <p className="mt-4 max-w-2xl text-base leading-relaxed text-white/80">{activeStep.detail}</p>
                  </div>
                </div>

                <div className="rounded-[28px] border border-white/10 bg-white/7 p-6">
                  <div className="mb-3 flex items-center gap-2 text-[11px] font-bold uppercase tracking-[0.22em] text-white/55">
                    <FileCheck size={14} />
                    Current milestone
                  </div>
                  <p className="text-sm leading-relaxed text-white/78">{activeStep.description}</p>
                  <div className="mt-4 flex flex-wrap gap-2">
                    {activeStep.chips.map((chip) => (
                      <span key={chip} className="rounded-full border border-white/10 bg-white/8 px-3 py-1.5 text-[11px] font-semibold text-white/85">
                        {chip}
                      </span>
                    ))}
                  </div>
                </div>
              </div>

              <div className="mt-12">
                <div className="relative">
                  <div className="absolute left-[4%] right-[4%] top-8 h-px bg-white/12" />
                  <div
                    className="absolute left-[4%] top-8 h-px rounded-full bg-gradient-to-r from-[#C96557] via-[#E1A57F] to-[#F4D2C1] shadow-[0_0_18px_rgba(201,101,87,0.35)]"
                    style={{ width: `${Math.max(progress * 92, 2)}%` }}
                  />

                  <div className="grid grid-cols-8 gap-3">
                    {journeySteps.map((step, index) => {
                      const threshold = index / Math.max(journeySteps.length - 1, 1);
                      const localProgress = clamp((progress - threshold + 0.14) / 0.14, 0, 1);
                      const isActive = index <= activeIndex;
                      const Icon = step.icon;

                      return (
                        <div key={step.title} className="flex flex-col items-center">
                          <div
                            className="relative z-10 flex h-16 w-16 items-center justify-center rounded-[22px] border transition-all duration-300"
                            style={{
                              opacity: 0.35 + localProgress * 0.65,
                              transform: `translateY(${(1 - localProgress) * 12}px) scale(${0.9 + localProgress * 0.1})`,
                              borderColor: isActive ? "rgba(201,101,87,0.65)" : "rgba(255,255,255,0.10)",
                              background: isActive ? "rgba(255,245,241,0.10)" : "rgba(255,255,255,0.05)",
                              boxShadow: isActive ? "0 18px 40px rgba(201,101,87,0.18)" : "none"
                            }}
                          >
                            <Icon size={22} className={isActive ? "text-[#F8D4C7]" : "text-white/55"} />
                          </div>

                          <div className="mt-4 px-2 text-center">
                            <div className={`text-[10px] font-bold uppercase tracking-[0.2em] ${isActive ? "text-[#F8D4C7]" : "text-white/42"}`}>
                              {step.phase}
                            </div>
                            <div className={`mt-2 text-xs font-semibold leading-relaxed ${isActive ? "text-white" : "text-white/55"}`}>
                              {step.title}
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>

                <div className="mt-8 grid grid-cols-4 gap-3">
                  {journeySteps.map((step, index) => {
                    const isVisible = index <= activeIndex;

                    return (
                      <div
                        key={`${step.title}-summary`}
                        className="rounded-[22px] border px-4 py-4 transition-all duration-300"
                        style={{
                          opacity: isVisible ? 1 : 0.34,
                          borderColor: isVisible ? "rgba(255,255,255,0.10)" : "rgba(255,255,255,0.06)",
                          background: isVisible ? "rgba(255,255,255,0.07)" : "rgba(255,255,255,0.03)"
                        }}
                      >
                        <div className="text-[10px] font-bold uppercase tracking-[0.2em] text-white/45">{step.phase}</div>
                        <p className="mt-2 text-sm leading-relaxed text-white/78">{step.description}</p>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="space-y-4 md:hidden">
        {journeySteps.map((step) => {
          const Icon = step.icon;

          return (
            <div key={step.title} className="rounded-[28px] border border-[#EAE6DF]/70 bg-white p-6 shadow-[0_18px_40px_rgba(0,0,0,0.05)]">
              <div className="flex items-start justify-between gap-4">
                <div className="text-[10px] font-bold uppercase tracking-[0.22em] text-[#6B6B6B]">{step.phase}</div>
                <div className="flex h-11 w-11 items-center justify-center rounded-2xl border border-[#EAE6DF] bg-[#FCFBF8] text-[#C96557]">
                  <Icon size={18} />
                </div>
              </div>
              <h3 className="mt-3 text-xl font-black tracking-tight text-[#2E2E2E]">{step.title}</h3>
              <p className="mt-3 text-sm leading-relaxed text-[#6B6B6B]">{step.detail}</p>
              <div className="mt-4 flex flex-wrap gap-2">
                {step.chips.map((chip) => (
                  <span key={chip} className="rounded-full border border-[#EAE6DF] bg-[#FCFBF8] px-3 py-1.5 text-[11px] font-semibold text-[#2E2E2E]">
                    {chip}
                  </span>
                ))}
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}
