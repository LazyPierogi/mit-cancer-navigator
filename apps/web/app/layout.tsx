import type { Metadata } from "next";
import type { ReactNode } from "react";
import "./globals.css";
import { STYLES } from "@/lib/theme";
import { Header } from "@/components/Header";

export const metadata: Metadata = {
  title: "NSCLC Navigator",
  description: "Deterministic Evidence Engine for Lung Cancer Treatment"
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;900&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className={`min-h-screen ${STYLES.bg} font-sans ${STYLES.textMain} flex flex-col selection:bg-[#C96557] selection:text-white`}>
        <Header />

        <main className="flex-1 max-w-[1400px] mx-auto w-full px-8 py-12">
          {children}
        </main>

        {/* Editorial Footer */}
        <footer className="bg-[#2E2E2E] text-[#6B6B6B] py-16 mt-20 border-t-[6px] border-[#C96557]">
          <div className="max-w-[1400px] mx-auto px-8 grid grid-cols-1 md:grid-cols-3 gap-8 items-center">
            <div className="flex items-center gap-4">
              <div className="w-3 h-3 rounded-full bg-[#E8F2EC] animate-pulse shadow-[0_0_12px_rgba(232,242,236,0.4)]" />
              <span className="text-[11px] font-bold uppercase tracking-[0.2em] text-[#EAE6DF]">System Integrity Verified</span>
            </div>
            <div className="text-[11px] font-medium text-[#EAE6DF]/60 text-center uppercase tracking-[0.2em] leading-loose">
              Project: NSCLC Treatment Navigator<br />
              Team 3: BUNDYRA, WIDMER, ESPELAND, LEŚNIEWSKI, RIEKEN, THEIS.
            </div>
            <div className="flex justify-end gap-8">
              <button className="text-[11px] font-bold hover:text-[#FFFFFF] transition-colors uppercase tracking-[0.2em]">API Docs</button>
              <button className="text-[11px] font-bold hover:text-[#FFFFFF] transition-colors uppercase tracking-[0.2em]">Logs</button>
              <button className="text-[11px] font-bold hover:text-[#FFFFFF] transition-colors uppercase tracking-[0.2em]">ESMO V2024</button>
            </div>
          </div>
        </footer>
      </body>
    </html>
  );
}
