import type { Metadata } from "next";
import { Anton, Inter } from "next/font/google";
import Link from "next/link";
import "./globals.css";

const anton = Anton({ weight: "400", subsets: ["latin"], variable: "--font-anton" });
const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });

export const metadata: Metadata = {
  title: "DropTable Records",
  description: "A record label for codebases. Sing your repo. Drop a track.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${anton.variable} ${inter.variable}`}>
      <body className="grain grain-fixed min-h-screen flex flex-col">
        <header className="sticky top-0 z-40 border-b border-line bg-paper/95 backdrop-blur-sm">
          <nav className="mx-auto flex max-w-7xl items-baseline justify-between gap-4 px-5 py-4 sm:gap-6">
            <Link href="/" className="font-display display-tight text-xl text-ink">
              DROPTABLE&nbsp;<span className="text-cobalt">RECORDS</span>
              <span className="text-gold">;</span>
            </Link>
            <div className="flex items-baseline gap-4 text-xs uppercase tracking-[0.14em] text-ink-dim sm:gap-6 sm:tracking-[0.2em]">
              <Link
                href="/roster"
                className="whitespace-nowrap underline-offset-4 decoration-cobalt transition-colors hover:text-cobalt hover:underline"
              >
                Roster
              </Link>
              <Link
                href="/sources"
                className="whitespace-nowrap underline-offset-4 decoration-cobalt transition-colors hover:text-cobalt hover:underline"
              >
                Sources
              </Link>
              <Link
                href="/#sign"
                className="whitespace-nowrap underline-offset-4 decoration-cobalt transition-colors hover:text-cobalt hover:underline"
              >
                Sing a repo
              </Link>
            </div>
          </nav>
          <div className="rule-double" />
        </header>

        <main className="flex-1">{children}</main>

        <footer className="border-t border-line bg-card px-5 py-8">
          <div className="mx-auto max-w-7xl">
            <div className="rule-double mb-5" />
            <div className="flex flex-wrap items-baseline justify-between gap-4 text-xs">
              <p className="font-display display-tight text-sm text-ink">
                DROPTABLE <span className="text-cobalt">RECORDS</span>
              </p>
              <p className="mono-label text-[11px] text-ink-dim">
                Est. 2026 — Every repo has a song in it
              </p>
              <p className="mono-label text-[11px] text-cobalt">
                DROP TABLE records; -- 0 rows returned
              </p>
            </div>
          </div>
        </footer>
      </body>
    </html>
  );
}
