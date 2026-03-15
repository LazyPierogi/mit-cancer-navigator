import React, { useState } from 'react';
import {
    Filter,
    ChevronRight,
    ChevronDown,
    ExternalLink,
    ShieldCheck,
    AlertTriangle,
    Info,
    BookOpen,
    CheckCircle2,
    Clock,
    FlaskConical,
    Award,
    ArrowRight,
    Database,
    Lock,
    UserCircle,
    Plus
} from 'lucide-react';

/**
 * EDITORIAL & WARM PRECISION THEME
 * Colors: Linen White, Graphite, Warm Slate, Clay Red
 * Status: Soft Sage, Soft Coral, Paper Strong
 */
const STYLES = {
    // Base Palette
    bg: 'bg-[#F9F8F6]', // Linen White
    surface: 'bg-[#FFFFFF]', // Pure White
    border: 'border-[#EAE6DF]', // Muted Sand
    borderLight: 'border-[#EAE6DF]/60',

    // Typography
    textMain: 'text-[#2E2E2E]', // Graphite
    textMuted: 'text-[#6B6B6B]', // Warm Slate
    textLight: 'text-[#6B6B6B]/70', // Warm Slate transparent

    // Brand / General Accents
    primaryBg: 'bg-[#C96557]',
    primaryText: 'text-[#C96557]',
    primaryLight: 'bg-[#C96557]/10',
    primaryBorder: 'border-[#C96557]',

    // Patient Profile Specific (Accent)
    accentBg: 'bg-[#C96557]', // Focus color for Patient Profile filters
    accentText: 'text-[#C96557]',
    accentLight: 'bg-[#C96557]/10',
    accentBorder: 'border-[#C96557]',

    // ERS Score Specific
    ersText: 'text-[#C96557]', // Color for the ERS numerical value
    ersBg: 'bg-[#C96557]',    // Color for the ERS progress bar

    // Interactions & Shapes
    hoverBg: 'hover:bg-[#F9F8F6]',
    ring: 'ring-[#C96557]/20',
    radiusMain: 'rounded-3xl',
    radiusCard: 'rounded-2xl',
    radiusChip: 'rounded-xl',

    // Custom Editorial Shadows & Transforms
    shadow: 'shadow-[0_4px_24px_rgba(0,0,0,0.04)]',
    cardHover: 'transition-all duration-300 ease-in-out hover:-translate-y-[2px] hover:shadow-[0_8px_32_rgba(0,0,0,0.08)]'
};

// --- Mock Data & Constants ---
const HISTOLOGY_OPTIONS = ["Adenocarcinoma", "Squamous Cell", "Non Squamous"];
const BIOMARKERS = ["EGFR+", "ALK+", "ROS1+", "PD-L1 > 50%", "Wild Type"];
const LINES_OF_THERAPY = ["1st Line", "2nd Line", "Later Line", "Adjuvant", "Consolidation"];

const PATIENT_PRESETS = [
    { id: 1, name: "MR. WAYNE", desc: "Metastatic adeno · 1L · PD-L1-high · pan-driver negative", data: { histology: 'Adenocarcinoma', biomarker: 'PD-L1 > 50%', line: '1st Line', custom: '' } },
    { id: 2, name: "MR. STARK", desc: "Locally advanced squamous · post-CRT consolidation", data: { histology: 'Squamous Cell', biomarker: 'Wild Type', line: 'Consolidation', custom: 'Post chemoradiation' } },
    { id: 3, name: "MRS. DOUBTFIRE", desc: "Early adeno · resected · adjuvant EGFR-positive", data: { histology: 'Adenocarcinoma', biomarker: 'EGFR+', line: 'Adjuvant', custom: 'Post surgery' } },
];

const MOCK_EVIDENCE = [
    {
        id: 1,
        title: "Pembrolizumab plus Chemotherapy in Metastatic NSCLC: 5-Year Follow-up",
        authors: "Rodriguez et al.",
        journal: "Journal of Clinical Oncology",
        year: 2024,
        type: "Systematic Review",
        sampleSize: 1240,
        ers: 58,
        status: "Aligned",
        tags: ["Adenocarcinoma", "1st Line", "PD-L1 > 50%"],
        abstract: "A comprehensive systematic review of long-term outcomes for pembrolizumab combination therapies, demonstrating sustained overall survival benefits across key histology cohorts...",
        metrics: { methodology: 20, robustness: 15, recency: 10, credibility: 13 }
    },
    {
        id: 2,
        title: "New Tyrosine Kinase Inhibitor (TKI-X) vs. Standard Docetaxel in Pre-treated Patients",
        authors: "Chen et al.",
        journal: "The Lancet Oncology",
        year: 2023,
        type: "RCT",
        sampleSize: 450,
        ers: 42,
        status: "In Conflict",
        tags: ["Squamous only", "2nd Line", "EGFR+"],
        abstract: "Phase III trial showing non-inferiority in progression-free survival but increased toxicity profiles and adverse events compared to existing ESMO recommendations...",
        metrics: { methodology: 15, robustness: 10, recency: 8, credibility: 9 }
    },
    {
        id: 3,
        title: "Impact of Performance Status on Targeted Therapy Efficacy",
        authors: "Schmidt et al.",
        journal: "Annals of Oncology",
        year: 2024,
        type: "Observational",
        sampleSize: 2100,
        ers: 35,
        status: "Guideline-Silent",
        tags: ["Adenocarcinoma", "EGFR+", "1st Line"],
        abstract: "Large-scale observational study exploring variables and sub-populations not currently addressed in detail by ESMO 2023 guidelines regarding performance status modifiers...",
        metrics: { methodology: 5, robustness: 15, recency: 10, credibility: 5 }
    }
];

// --- Sub-Components ---

const StatBadge = ({ icon: Icon, label, value, accentColor }) => (
    <div className={`flex items-center gap-2 px-4 py-2 ${STYLES.radiusChip} ${STYLES.surface} ${STYLES.shadow}`}>
        <Icon size={14} className={accentColor} />
        <span className={`text-xs font-semibold uppercase tracking-wider ${STYLES.textMuted}`}>{label}:</span>
        <span className={`text-xs font-bold ${STYLES.textMain}`}>{value}</span>
    </div>
);

const EvidenceCard = ({ item }) => {
    const [expanded, setExpanded] = useState(false);

    const statusConfig = {
        'Aligned': { colors: 'text-[#2D5940] bg-[#E8F2EC]', icon: <CheckCircle2 size={16} /> },
        'In Conflict': { colors: 'text-[#A63D2F] bg-[#FBEAE5]', icon: <AlertTriangle size={16} /> },
        'Guideline-Silent': { colors: 'text-[#6B6B6B] bg-[#F0EBE3]', icon: <Info size={16} /> }
    };

    const status = statusConfig[item.status];

    return (
        <div className={`${STYLES.radiusCard} ${STYLES.surface} ${STYLES.shadow} ${STYLES.cardHover} border-0 overflow-hidden`}>
            <div className="p-6 flex gap-6 cursor-pointer relative z-10" onClick={() => setExpanded(!expanded)}>
                {/* ERS Score Pillar */}
                <div className={`flex flex-col items-center justify-center w-20 border-r pr-5 ${STYLES.borderLight}`}>
                    <div className={`text-3xl font-black ${STYLES.ersText} leading-none tracking-tight`}>{item.ers}</div>
                    <div className={`text-[10px] font-bold ${STYLES.textLight} mt-1 text-center leading-tight uppercase`}>ERS Score</div>
                    <div className={`w-full ${STYLES.bg} h-1.5 rounded-full mt-4 overflow-hidden`}>
                        <div className={`${STYLES.ersBg} h-full transition-all duration-500`} style={{ width: `${(item.ers / 60) * 100}%` }}></div>
                    </div>
                </div>

                {/* Info Area */}
                <div className="flex-1">
                    <div className="flex items-start justify-between mb-2">
                        <h3 className={`text-lg font-bold ${STYLES.textMain} leading-tight pr-4`}>{item.title}</h3>
                        <div className={`flex items-center gap-1.5 px-3 py-1.5 ${STYLES.radiusChip} text-[10px] font-bold border-0 whitespace-nowrap uppercase tracking-wide ${status.colors}`}>
                            {status.icon}
                            {item.status}
                        </div>
                    </div>

                    <div className={`flex flex-wrap gap-4 text-sm ${STYLES.textMuted} mb-4`}>
                        <span className={`font-semibold ${STYLES.textMain}`}>{item.authors}</span>
                        <span className="flex items-center gap-1.5"><BookOpen size={14} /> {item.journal}</span>
                        <span className="flex items-center gap-1.5"><Clock size={14} /> {item.year}</span>
                    </div>

                    <div className="flex flex-wrap gap-2">
                        {item.tags.map(tag => (
                            <span key={tag} className={`px-3 py-1 ${STYLES.bg} ${STYLES.textMuted} ${STYLES.radiusChip} text-[10px] font-semibold uppercase tracking-tight`}>
                                {tag}
                            </span>
                        ))}
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
                                <h4 className={`text-xs font-bold ${STYLES.textMuted} uppercase tracking-widest`}>Clinical Abstract</h4>
                                <p className={`text-sm ${STYLES.textMain} leading-relaxed opacity-90`}>{item.abstract}</p>
                                <button className={`flex items-center gap-2 text-sm font-bold ${STYLES.primaryText} hover:opacity-70 transition-opacity mt-4`}>
                                    View on PubMed <ExternalLink size={14} />
                                </button>
                            </div>

                            <div className={`${STYLES.surface} p-5 ${STYLES.radiusCard} ${STYLES.shadow}`}>
                                <h4 className={`text-xs font-bold ${STYLES.textMuted} uppercase tracking-widest mb-5`}>ERS Composition</h4>
                                <div className="space-y-4">
                                    <MetricBar label="Methodology" value={item.metrics.methodology} max={20} color="bg-[#5C7C8A]" />
                                    <MetricBar label="Robustness" value={item.metrics.robustness} max={15} color="bg-[#8A9A5B]" />
                                    <MetricBar label="Recency" value={item.metrics.recency} max={10} color="bg-[#D4A373]" />
                                    <MetricBar label="Credibility" value={item.metrics.credibility} max={15} color={STYLES.ersBg} />
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

const MetricBar = ({ label, value, max, color }) => (
    <div className="space-y-1.5">
        <div className={`flex justify-between text-[10px] font-bold ${STYLES.textMuted} tracking-wide`}>
            <span>{label.toUpperCase()}</span>
            <span>{value}/{max}</span>
        </div>
        <div className={`w-full ${STYLES.bg} h-1.5 rounded-full overflow-hidden`}>
            <div className={`${color} h-full transition-all duration-700`} style={{ width: `${(value / max) * 100}%` }}></div>
        </div>
    </div>
);

// --- Main Application ---

export default function App() {
    const [activePreset, setActivePreset] = useState(1);
    const [filters, setFilters] = useState(PATIENT_PRESETS[0].data);
    const [customInput, setCustomInput] = useState(PATIENT_PRESETS[0].data.custom);

    const handlePresetChange = (preset) => {
        setActivePreset(preset.id);
        setFilters(preset.data);
        setCustomInput(preset.data.custom);
    };

    const handleCustomInput = (e) => {
        setCustomInput(e.target.value);
        setActivePreset(null);
    };

    const handleChipClick = (category, value) => {
        setFilters({ ...filters, [category]: value });
        setActivePreset(null);
    };

    return (
        <div className={`min-h-screen ${STYLES.bg} font-sans ${STYLES.textMain} flex flex-col selection:bg-[#C96557] selection:text-white`}>

            {/* Editorial Header */}
            <header className={`${STYLES.surface} border-b ${STYLES.border} sticky top-0 z-40`}>
                <div className="max-w-7xl mx-auto px-6 h-20 flex items-center justify-between">
                    <div className="flex items-center gap-4">
                        <div className={`${STYLES.primaryBg} p-2.5 ${STYLES.radiusChip} text-white ${STYLES.shadow}`}>
                            <ShieldCheck size={26} strokeWidth={1.5} />
                        </div>
                        <div>
                            <h1 className={`font-semibold text-2xl tracking-tight ${STYLES.textMain} leading-none`}>NSCLC Navigator</h1>
                            <p className={`text-[10px] font-bold ${STYLES.textLight} tracking-[0.2em] mt-1.5 uppercase`}>Deterministic Evidence Engine</p>
                        </div>
                    </div>

                    <div className="flex items-center gap-8">
                        <div className={`hidden md:flex items-center gap-2 px-4 py-2 ${STYLES.radiusChip} bg-[#E8F2EC] text-[#2D5940]`}>
                            <Database size={16} />
                            <span className="text-[10px] font-bold uppercase tracking-wider">Engine: Live V2.1</span>
                        </div>

                        <div className={`h-10 w-px ${STYLES.border}`} />

                        <div className="flex items-center gap-4">
                            <div className="text-right">
                                <p className={`text-sm font-semibold ${STYLES.textMain}`}>Dr. Sarah Jenkins</p>
                                <p className={`text-[11px] ${STYLES.textMuted}`}>Thoracic Oncology Unit</p>
                            </div>
                            <div className={`w-12 h-12 ${STYLES.radiusChip} ${STYLES.bg} border ${STYLES.border} flex items-center justify-center font-bold ${STYLES.textMuted}`}>
                                SJ
                            </div>
                        </div>
                    </div>
                </div>
            </header>

            {/* Main Content Area */}
            <main className="flex-1 max-w-7xl mx-auto w-full px-6 py-10 grid grid-cols-12 gap-10">

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
                                {PATIENT_PRESETS.map(preset => (
                                    <button
                                        key={preset.id}
                                        onClick={() => handlePresetChange(preset)}
                                        className={`flex flex-col items-center justify-center p-3 ${STYLES.radiusCard} border transition-all duration-300 ${activePreset === preset.id ? `${STYLES.accentBg} text-white border-transparent ${STYLES.shadow}` : `${STYLES.bg} ${STYLES.textMuted} ${STYLES.borderLight} ${STYLES.hoverBg}`}`}
                                    >
                                        <span className="text-xs font-bold uppercase tracking-wide">{preset.name}</span>
                                        <span className={`text-[9px] mt-0.5 text-center leading-relaxed ${activePreset === preset.id ? 'text-white/80' : STYLES.textLight}`}>{preset.desc}</span>
                                    </button>
                                ))}
                            </div>
                        </div>

                        <div className={`h-px w-full ${STYLES.borderLight} mb-8`} />

                        {/* Explicit Tag Selection */}
                        <div className="space-y-8">
                            <div className="space-y-3">
                                <label className={`text-[11px] font-bold ${STYLES.textLight} uppercase tracking-widest`}>Histology</label>
                                <div className="flex flex-wrap gap-2.5">
                                    {HISTOLOGY_OPTIONS.map(opt => (
                                        <button
                                            key={opt}
                                            onClick={() => handleChipClick('histology', opt)}
                                            className={`px-4 py-2 ${STYLES.radiusChip} text-xs transition-all font-medium border ${filters.histology === opt ? `${STYLES.accentBg} text-white border-transparent ${STYLES.shadow}` : `${STYLES.surface} ${STYLES.textMuted} ${STYLES.borderLight} ${STYLES.hoverBg}`}`}
                                        >
                                            {opt}
                                        </button>
                                    ))}
                                </div>
                            </div>

                            <div className="space-y-3">
                                <label className={`text-[11px] font-bold ${STYLES.textLight} uppercase tracking-widest`}>Biomarker Profile</label>
                                <div className="flex flex-wrap gap-2.5">
                                    {BIOMARKERS.map(opt => (
                                        <button
                                            key={opt}
                                            onClick={() => handleChipClick('biomarker', opt)}
                                            className={`px-4 py-2 ${STYLES.radiusChip} text-xs transition-all font-medium border ${filters.biomarker === opt ? `${STYLES.accentBg} text-white border-transparent ${STYLES.shadow}` : `${STYLES.surface} ${STYLES.textMuted} ${STYLES.borderLight} ${STYLES.hoverBg}`}`}
                                        >
                                            {opt}
                                        </button>
                                    ))}
                                </div>
                            </div>

                            <div className="space-y-3">
                                <label className={`text-[11px] font-bold ${STYLES.textLight} uppercase tracking-widest`}>Line of Therapy</label>
                                <div className="flex flex-wrap gap-2.5">
                                    {LINES_OF_THERAPY.map(opt => (
                                        <button
                                            key={opt}
                                            onClick={() => handleChipClick('line', opt)}
                                            className={`px-4 py-2 ${STYLES.radiusChip} text-xs transition-all font-medium border ${filters.line === opt ? `${STYLES.accentBg} text-white border-transparent ${STYLES.shadow}` : `${STYLES.surface} ${STYLES.textMuted} ${STYLES.borderLight} ${STYLES.hoverBg}`}`}
                                        >
                                            {opt}
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
                                        onChange={handleCustomInput}
                                        className={`w-full ${STYLES.bg} border ${STYLES.border} ${STYLES.textMain} ${STYLES.radiusCard} pl-10 pr-4 py-3 text-sm font-medium focus:ring-1 ${STYLES.ring} focus:border-[#C96557] outline-none transition-all placeholder:font-normal placeholder:opacity-60`}
                                    />
                                </div>
                            </div>
                        </div>

                        <div className={`mt-10 p-5 ${STYLES.radiusCard} bg-[#FBEAE5] text-[#A63D2F]`}>
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

                    {/* Summary Dashboard */}
                    <div className="flex flex-wrap items-center gap-5">
                        <StatBadge icon={FlaskConical} label="Retrieved" value="48 Studies" accentColor={STYLES.primaryText} />
                        <StatBadge icon={Award} label="Avg ERS" value="42.5" accentColor="text-[#6B6B6B]" />
                        <StatBadge icon={ShieldCheck} label="Recall Rate" value="98.2%" accentColor="text-[#2D5940]" />

                        <div className="ml-auto flex items-center gap-3">
                            <span className={`text-[10px] font-bold ${STYLES.textLight} uppercase tracking-widest`}>Sorted By</span>
                            <select className={`bg-transparent text-xs font-bold ${STYLES.primaryText} outline-none cursor-pointer hover:underline`}>
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
                            <span className={`text-[10px] font-bold ${STYLES.primaryText} ${STYLES.primaryLight} px-3 py-1 ${STYLES.radiusChip} uppercase border-0`}>Verified Logic</span>
                        </div>

                        <div className="grid gap-6">
                            {MOCK_EVIDENCE.map(item => (
                                <EvidenceCard key={item.id} item={item} />
                            ))}
                        </div>

                        <button className={`w-full py-5 border ${STYLES.border} ${STYLES.radiusCard} ${STYLES.textMuted} text-sm font-semibold ${STYLES.surface} ${STYLES.cardHover} transition-all flex items-center justify-center gap-3 group`}>
                            Expand Dataset <ArrowRight size={18} className="group-hover:translate-x-1 transition-transform" />
                        </button>
                    </div>

                    {/* Stance Matrix Table */}
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
                                    <tr className={`border-t ${STYLES.borderLight} ${STYLES.hoverBg} transition-colors`}>
                                        <td className={`px-8 py-6 font-semibold ${STYLES.textMain}`}>1st Line Pembrolizumab</td>
                                        <td className="px-8 py-6"><span className={`px-3 py-1.5 bg-[#E8F2EC] text-[#2D5940] ${STYLES.radiusChip} text-[10px] font-bold uppercase tracking-wide`}>Recommended</span></td>
                                        <td className={`px-8 py-6 ${STYLES.textMuted}`}>12 Studies (Aligned)</td>
                                        <td className="px-8 py-6"><span className={`text-xs font-bold ${STYLES.textLight} uppercase tracking-widest`}>Low (0.0)</span></td>
                                    </tr>
                                    <tr className={`border-t ${STYLES.borderLight} ${STYLES.hoverBg} transition-colors`}>
                                        <td className={`px-8 py-6 font-semibold ${STYLES.textMain}`}>TKI-X Post-Immunotherapy</td>
                                        <td className="px-8 py-6"><span className={`px-3 py-1.5 bg-[#F0EBE3] text-[#6B6B6B] ${STYLES.radiusChip} text-[10px] font-bold uppercase tracking-wide`}>Silent / No Data</span></td>
                                        <td className={`px-8 py-6 ${STYLES.textMuted}`}>3 Studies (Novel)</td>
                                        <td className="px-8 py-6"><span className="text-xs font-bold text-[#6B6B6B] uppercase tracking-widest">Moderate</span></td>
                                    </tr>
                                    <tr className={`border-t ${STYLES.borderLight} bg-[#FBEAE5]/30 hover:bg-[#FBEAE5]/50 transition-colors`}>
                                        <td className={`px-8 py-6 font-semibold ${STYLES.textMain}`}>Metronomic Chemotherapy</td>
                                        <td className="px-8 py-6"><span className={`px-3 py-1.5 bg-[#FBEAE5] text-[#A63D2F] ${STYLES.radiusChip} text-[10px] font-bold uppercase tracking-wide`}>Not Advised</span></td>
                                        <td className={`px-8 py-6 ${STYLES.textMuted}`}>2 Studies (Conflict)</td>
                                        <td className="px-8 py-6"><span className="text-xs font-bold text-[#A63D2F] flex items-center gap-2 uppercase tracking-widest"><AlertTriangle size={14} /> Critical</span></td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                    </section>

                </div>
            </main>

            {/* Editorial Footer */}
            <footer className="bg-[#2E2E2E] text-[#6B6B6B] py-12 mt-16 border-t-[6px] border-[#C96557]">
                <div className="max-w-7xl mx-auto px-6 grid grid-cols-1 md:grid-cols-3 gap-8 items-center">
                    <div className="flex items-center gap-4">
                        <div className="w-2.5 h-2.5 rounded-full bg-[#E8F2EC] animate-pulse shadow-[0_0_10px_rgba(232,242,236,0.3)]" />
                        <span className="text-[10px] font-bold uppercase tracking-[0.2em] text-[#EAE6DF]">System Integrity Verified</span>
                    </div>
                    <div className="text-[10px] font-medium text-[#EAE6DF]/60 text-center uppercase tracking-[0.2em] leading-loose">
                        Project: NSCLC Treatment Navigator<br />
                        Team 3: BUNDYRA, WIDMER, ESPELAND, LEŚNIEWSKI, RIEKEN, THEIS.
                    </div>
                    <div className="flex justify-end gap-6">
                        <button className="text-[10px] font-bold hover:text-[#FFFFFF] transition-colors uppercase tracking-[0.2em]">API Docs</button>
                        <button className="text-[10px] font-bold hover:text-[#FFFFFF] transition-colors uppercase tracking-[0.2em]">Logs</button>
                        <button className="text-[10px] font-bold hover:text-[#FFFFFF] transition-colors uppercase tracking-[0.2em]">ESMO V2024</button>
                    </div>
                </div>
            </footer>
        </div>
    );
}
