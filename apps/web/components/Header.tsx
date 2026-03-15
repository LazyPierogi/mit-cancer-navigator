"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { ShieldCheck, Database, LayoutDashboard, Telescope, FileText } from "lucide-react";
import { STYLES } from "@/lib/theme";

const navItems = [
    { href: "/", label: "Navigator", icon: Telescope },
    { href: "/labs", label: "Labs", icon: LayoutDashboard },
    { href: "/about", label: "About", icon: FileText }
];

export function Header() {
    const pathname = usePathname();

    return (
        <header className={`${STYLES.surface} border-b ${STYLES.border} sticky top-0 z-40`}>
            <div className="max-w-[1400px] w-full mx-auto px-8 h-24 flex items-center justify-between">
                <Link href="/" className="flex items-center gap-4 hover:opacity-80 transition-opacity">
                    <div className={`${STYLES.primaryBg} p-3 ${STYLES.radiusChip} text-white ${STYLES.shadow}`}>
                        <ShieldCheck size={28} strokeWidth={1.5} />
                    </div>
                    <div>
                        <h1 className={`font-semibold text-2xl tracking-tight ${STYLES.textMain} leading-none`}>NSCLC Navigator</h1>
                        <p className={`text-[11px] font-bold ${STYLES.textLight} tracking-[0.2em] mt-1.5 uppercase`}>Deterministic Evidence Engine</p>
                    </div>
                </Link>

                <nav className="hidden md:flex items-center gap-12 absolute left-1/2 -translate-x-1/2 h-full">
                    {navItems.map((item) => {
                        const Icon = item.icon;
                        const isActive = pathname === item.href || (item.href !== '/' && pathname?.startsWith(item.href));
                        return (
                            <Link href={item.href} key={item.href} className={`flex flex-col items-center justify-center h-full border-b-[3px] transition-colors group ${isActive ? 'border-[#C96557]' : 'border-transparent hover:border-[#C96557]/30'}`}>
                                <div className={`flex items-center gap-2 text-sm font-bold uppercase tracking-widest ${isActive ? 'text-[#C96557]' : `${STYLES.textMuted} group-hover:${STYLES.textMain}`}`}>
                                    <Icon size={16} />
                                    {item.label}
                                </div>
                            </Link>
                        );
                    })}
                </nav>

                <div className="flex items-center gap-8">
                    <div className="flex items-center gap-4">
                        <div className="text-right">
                            <p className={`text-[15px] font-bold ${STYLES.textMain}`}>MIT User</p>
                            <p className={`text-xs font-medium ${STYLES.textMuted}`}>MIT Student Class</p>
                        </div>
                        <div className={`w-12 h-12 ${STYLES.radiusChip} bg-[#F9F8F6] border ${STYLES.border} flex items-center justify-center text-sm font-bold ${STYLES.textMuted}`}>
                            MIT
                        </div>
                    </div>
                </div>
            </div>
        </header>
    );
}
