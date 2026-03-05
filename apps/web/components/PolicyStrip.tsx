import { ShieldCheck, Info, Database } from 'lucide-react';
import { STYLES } from '@/lib/theme';

type PolicyStripProps = {
  rulesetVersion: string;
  corpusVersion: string;
  uncertaintyFlags: string[];
};

export function PolicyStrip({ rulesetVersion, corpusVersion, uncertaintyFlags }: PolicyStripProps) {
  return (
    <div className={`w-fit flex flex-wrap items-center gap-4 px-5 py-2.5 ${STYLES.radiusChip} border ${STYLES.borderLight} bg-[#F9F8F6] text-[11px] font-bold uppercase tracking-wider ${STYLES.textMuted}`}>
      <div className="flex items-center gap-2">
        <ShieldCheck size={14} className={STYLES.primaryText} />
        <span>Ruleset:</span>
        <span className={STYLES.textMain}>{rulesetVersion}</span>
      </div>
      <div className={`h-4 w-px ${STYLES.borderLight}`} />
      <div className="flex items-center gap-2">
        <span>Corpus:</span>
        <span className={STYLES.textMain}>{corpusVersion}</span>
      </div>
      <div className={`h-4 w-px ${STYLES.borderLight}`} />
      <div className="flex items-center gap-2">
        <span>Scope:</span>
        <span className={STYLES.textMain}>NSCLC treatment evidence only</span>
      </div>
      <div className={`h-4 w-px ${STYLES.borderLight}`} />
      <div className="flex items-center gap-2 text-amber-600">
        <Info size={14} />
        <span>Uncertainty Flags:</span>
        <span className="text-amber-700">{uncertaintyFlags.length}</span>
      </div>
      <div className={`flex items-center gap-2 px-3 py-1.5 ${STYLES.radiusChip} bg-[#E8F2EC] text-[#2D5940]`}>
        <Database size={14} />
        <span className="text-[11px] font-bold uppercase tracking-wider">Engine: Live V2.1</span>
      </div>
    </div>
  );
}
