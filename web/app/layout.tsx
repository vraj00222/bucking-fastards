import type { Metadata } from "next";
import { Anton, Inter } from "next/font/google";
import Link from "next/link";
import "./globals.css";

const anton = Anton({ weight: "400", subsets: ["latin"], variable: "--font-anton" });
const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });

export const metadata: Metadata = {
  title: "DropTable Records",
  description: "A record label for codebases. Sign your repo. Drop a track.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${anton.variable} ${inter.variable}`}>
      <body className="grain grain-fixed min-h-screen flex flex-col">
        <header className="sticky top-0 z-40 border-b border-line bg-bg/90 backdrop-blur-sm">
          <nav className="mx-auto flex max-w-7xl items-baseline justify-between gap-6 px-5 py-4">
            <Link href="/" className="font-display display-tight text-xl tracking-wide">
              DROPTABLE&nbsp;RECORDS<span className="text-ink-dim">;</span>
            </Link>
            <div className="flex items-baseline gap-6 text-xs uppercase tracking-[0.2em] text-ink-dim">
              <Link href="/roster" className="hover:text-ink transition-colors">
                Roster
              </Link>
              <Link href="/sign" className="hover:text-ink transition-colors">
                Sign a repo
              </Link>
            </div>
          </nav>
        </header>

        <main className="flex-1">{children}</main>

        <footer className="border-t border-line px-5 py-8">
          <div className="mx-auto flex max-w-7xl flex-wrap items-baseline justify-between gap-4 text-xs text-ink-dim">
            <p className="font-display display-tight text-sm">DROPTABLE RECORDS</p>
            <p className="uppercase tracking-[0.2em]">Every repo has a song in it</p>
            <p className="font-mono">DROP TABLE records; -- 0 rows returned</p>
          </div>
        </footer>
      </body>
    </html>
  );
}
