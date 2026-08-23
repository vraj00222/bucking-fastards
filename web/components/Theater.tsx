"use client";

import { useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { useRouter } from "next/navigation";
import { presetFor } from "@/lib/presets";

type JobState = {
  stage: "starting" | "intel" | "lyrics" | "audio" | "done" | "error";
  fact?: string;
  title?: string;
  slug?: string;
  startedAt: number;
  stageTimes: Partial<Record<string, number>>;
  error?: string;
  log: string[];
  now: number;
};

const STAGES = [
  { key: "intel", label: "A&R is listening", sub: "reading the source" },
  { key: "lyrics", label: "Writing the track", sub: "Claude, ghostwriting" },
  { key: "audio", label: "In the booth", sub: "ACE-Step on a Modal L40S" },
  { key: "done", label: "Pressing vinyl", sub: "mastered, published to the roster" },
] as const;

export default function Theater({
  jobId,
  style,
  repo,
  onClose,
}: {
  jobId: string;
  style: string;
  repo: string;
  onClose: () => void;
}) {
  const { accent } = presetFor(style);
  const router = useRouter();
  const [job, setJob] = useState<JobState | null>(null);
  const [, setTick] = useState(0);
  const skew = useRef(0); // client clock minus server clock

  useEffect(() => {
    let live = true;
    const poll = async () => {
      try {
        const r = await fetch(`/api/status/${jobId}`);
        if (!r.ok) return;
        const j: JobState = await r.json();
        if (!live) return;
        skew.current = Date.now() - j.now;
        setJob(j);
      } catch {
        /* transient poll failure; next tick retries */
      }
    };
    poll();
    const p = setInterval(poll, 2000);
    const t = setInterval(() => setTick((n) => n + 1), 500);
    return () => {
      live = false;
      clearInterval(p);
      clearInterval(t);
    };
  }, [jobId]);

  // lock the page behind the overlay
  useEffect(() => {
    const prev = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = prev;
    };
  }, []);

  useEffect(() => {
    if (job?.stage === "done" && job.slug) {
      const t = setTimeout(() => router.push(`/track/${job.slug}`), 1800);
      return () => clearTimeout(t);
    }
  }, [job?.stage, job?.slug, router]);

  const now = () => Date.now() - skew.current;
  const failed = job?.stage === "error";
  // On error the job's stage is no longer a pipeline stage; use the last one reached.
  const stageIdx = failed
    ? STAGES.reduce((acc, s, i) => (job?.stageTimes[s.key] !== undefined ? i : acc), 0)
    : Math.max(0, STAGES.findIndex((s) => s.key === (job?.stage ?? "intel")));

  const secondsFor = (i: number): string => {
    if (!job) return "";
    const start = job.stageTimes[STAGES[i].key] ?? (i === 0 ? job.startedAt : undefined);
    if (start === undefined) return "";
    const next = i + 1 < STAGES.length ? job.stageTimes[STAGES[i + 1].key] : undefined;
    const end = next ?? job.stageTimes.error ?? now();
    return `${Math.max(0, Math.round((end - start) / 1000))}s`;
  };

  const totalS = job ? Math.max(0, Math.round((now() - job.startedAt) / 1000)) : 0;
  const progressPct =
    job?.stage === "done" ? 100 : ((stageIdx + 0.5) / STAGES.length) * 100;

  // Portal: escape the hero's z-10 stacking context so the overlay covers the nav.
  return createPortal(
    <div className="fixed inset-0 z-50 overflow-y-auto bg-paper">
      {/* backdrop: engraved vinyl grooves radiating from behind the record */}
      <div
        className="pointer-events-none fixed inset-0 opacity-[0.07]"
        style={{
          background:
            "repeating-radial-gradient(circle at 50% 30%, var(--cobalt) 0 1.5px, transparent 1.5px 28px)",
        }}
      />

      <div className="grain relative mx-auto flex min-h-full w-full max-w-3xl flex-col items-center px-5 py-14 text-center">
        <p className="mono-label text-[11px] text-cobalt">
          DropTable Records — session in progress
        </p>
        <p className="mt-2 font-mono text-xs text-ink-dim">{repo}</p>

        {/* vinyl: cobalt grooves, gold label center */}
        <div
          className="relative mt-10 h-56 w-56 rounded-full sm:h-64 sm:w-64"
          style={{ boxShadow: "0 2px 8px rgba(30,58,158,0.12)" }}
        >
          <div className={`vinyl-disc h-full w-full ${failed ? "" : "vinyl-spin"}`} />
          {/* label text sits still while the disc spins */}
          <div className="absolute left-1/2 top-1/2 flex h-[36%] w-[36%] -translate-x-1/2 -translate-y-1/2 flex-col items-center justify-center rounded-full">
            <span className="font-display text-[9px] uppercase leading-tight tracking-widest text-ink">
              DropTable
              <br />
              Records;
            </span>
            <span className="mt-1 h-2 w-2 rounded-full bg-paper" />
          </div>
        </div>

        {/* the reveal */}
        <div className="mt-10 min-h-[7rem]">
          {failed ? (
            <>
              <h2 className="font-display display-tight text-4xl text-ink sm:text-5xl">
                The session fell apart.
              </h2>
              <p className="mt-3 text-sm text-ink-dim">{job?.error}</p>
            </>
          ) : job?.title ? (
            <>
              <p className="mono-label text-[11px] text-cobalt">Now recording</p>
              <h2 className="font-display display-tight mt-2 text-4xl text-ink sm:text-5xl">
                {job.title}
              </h2>
            </>
          ) : (
            <h2 className="font-display display-tight text-4xl text-ink sm:text-5xl">
              Cutting a record…
            </h2>
          )}
          {job?.fact && !failed && (
            <div
              className="mx-auto mt-5 max-w-xl border-l-[3px] border-gold bg-card px-4 py-3 text-left font-mono text-xs leading-relaxed text-ink"
              style={{ boxShadow: "0 2px 8px rgba(30,58,158,0.12)" }}
            >
              <span className="text-ink-dim">A&amp;R found: </span>
              &ldquo;{job.fact}&rdquo;
            </div>
          )}
        </div>

        {/* cobalt progress hairline */}
        <div className="mt-8 h-px w-full max-w-md bg-line">
          <div
            className="h-px bg-cobalt transition-[width] duration-700"
            style={{ width: `${progressPct}%` }}
          />
        </div>

        {/* stages */}
        <div className="w-full max-w-md text-left">
          {STAGES.map((s, i) => {
            const state = failed
              ? i < stageIdx ? "done" : i === stageIdx ? "failed" : "pending"
              : i < stageIdx || job?.stage === "done"
                ? "done"
                : i === stageIdx
                  ? "active"
                  : "pending";
            return (
              <div
                key={s.key}
                className="flex items-baseline gap-4 border-b border-line py-3"
                style={{ opacity: state === "pending" ? 0.4 : 1 }}
              >
                <span
                  className="w-4 text-center font-mono text-xs"
                  style={{
                    color:
                      state === "failed"
                        ? accent
                        : state === "active"
                          ? "var(--cobalt)"
                          : state === "done"
                            ? "var(--gold)"
                            : "var(--ink-dim)",
                  }}
                >
                  {state === "done" ? "✓" : state === "failed" ? "✗" : state === "active" ? "●" : "○"}
                </span>
                <span className="font-display text-base uppercase tracking-wide text-ink">
                  {s.label}
                  {state === "active" && <span className="animate-pulse">…</span>}
                </span>
                <span className="text-xs text-ink-dim">{s.sub}</span>
                <span className="ml-auto font-mono text-xs text-ink-dim">
                  {state === "pending" ? "" : secondsFor(i)}
                </span>
              </div>
            );
          })}
          <div className="flex justify-between py-3 font-mono text-xs text-ink-dim">
            <span>studio time</span>
            <span>{totalS}s</span>
          </div>
        </div>

        {failed && (
          <div className="mt-6 w-full max-w-md text-left">
            <pre className="max-h-40 overflow-y-auto border border-line bg-card p-3 font-mono text-[11px] leading-relaxed text-ink-dim">
              {job?.log.slice(-8).join("\n")}
            </pre>
            <button
              onClick={onClose}
              className="mt-6 w-full border border-line px-6 py-3 font-display text-sm uppercase tracking-widest text-ink transition-colors hover:border-cobalt"
            >
              Back to the desk
            </button>
          </div>
        )}

        {job?.stage === "done" && (
          <p className="mono-label mt-6 text-[11px] text-cobalt">
            Signed. Taking you to the release…
          </p>
        )}
      </div>
    </div>,
    document.body,
  );
}
