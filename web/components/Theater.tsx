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

  // Portal: escape the hero's z-10 stacking context so the overlay covers the nav.
  return createPortal(
    <div className="fixed inset-0 z-50 overflow-y-auto bg-bg">
      {/* backdrop: gallery painting, nearly swallowed by the dark */}
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        src="/art/bg2.jpg"
        alt=""
        className="pointer-events-none fixed inset-0 h-full w-full object-cover opacity-[0.14]"
        style={{ filter: "grayscale(0.7) contrast(1.1)" }}
      />
      <div
        className="pointer-events-none fixed inset-0"
        style={{
          background: `radial-gradient(60% 50% at 50% 30%, ${accent}14, transparent 70%), linear-gradient(rgba(13,11,9,0.55), rgba(13,11,9,0.92))`,
        }}
      />

      <div className="grain relative mx-auto flex min-h-full w-full max-w-3xl flex-col items-center px-5 py-14 text-center">
        <p className="text-[11px] uppercase tracking-[0.35em] text-ink-dim">
          DropTable Records — session in progress
        </p>
        <p className="mt-2 font-mono text-xs text-ink-dim">{repo}</p>

        {/* vinyl */}
        <div className="relative mt-10 h-56 w-56 sm:h-64 sm:w-64">
          <div
            className={failed ? "h-full w-full rounded-full" : "vinyl-spin h-full w-full rounded-full"}
            style={{
              background:
                "repeating-radial-gradient(circle at 50% 50%, #181310 0 2.5px, #0a0806 2.5px 5px)",
              boxShadow: `0 0 90px ${accent}33, inset 0 0 40px rgba(0,0,0,0.8)`,
            }}
          >
            {/* light sheen across the grooves */}
            <div
              className="absolute inset-0 rounded-full"
              style={{
                background:
                  "conic-gradient(from 210deg, transparent 0deg, rgba(236,227,210,0.10) 25deg, transparent 60deg, transparent 180deg, rgba(236,227,210,0.06) 210deg, transparent 245deg)",
              }}
            />
            {/* center label */}
            <div
              className="absolute left-1/2 top-1/2 flex h-[38%] w-[38%] -translate-x-1/2 -translate-y-1/2 flex-col items-center justify-center rounded-full text-black"
              style={{ background: accent }}
            >
              <span className="font-display text-[9px] uppercase leading-tight tracking-widest">
                DropTable
                <br />
                Records;
              </span>
              <span className="mt-1 h-2 w-2 rounded-full bg-bg" />
            </div>
          </div>
        </div>

        {/* the reveal */}
        <div className="mt-10 min-h-[7rem]">
          {failed ? (
            <>
              <h2 className="font-display display-tight text-4xl text-paper sm:text-5xl">
                The session fell apart.
              </h2>
              <p className="mt-3 text-sm text-ink-dim">{job?.error}</p>
            </>
          ) : job?.title ? (
            <>
              <p className="text-[11px] uppercase tracking-[0.35em]" style={{ color: accent }}>
                Now recording
              </p>
              <h2 className="font-display display-tight mt-2 text-4xl text-paper sm:text-5xl">
                {job.title}
              </h2>
            </>
          ) : (
            <h2 className="font-display display-tight text-4xl text-paper sm:text-5xl">
              Cutting a record…
            </h2>
          )}
          {job?.fact && !failed && (
            <p className="mx-auto mt-4 max-w-xl text-sm leading-relaxed text-ink-dim">
              we found:{" "}
              <span className="italic text-ink">&ldquo;{job.fact}&rdquo;</span>
            </p>
          )}
        </div>

        {/* stages */}
        <div className="mt-8 w-full max-w-md text-left">
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
                style={{ opacity: state === "pending" ? 0.35 : 1 }}
              >
                <span
                  className="w-4 text-center font-mono text-xs"
                  style={{ color: state === "active" || state === "failed" ? accent : "var(--ink-dim)" }}
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
            <pre className="max-h-40 overflow-y-auto border border-line bg-bg-raised p-3 font-mono text-[11px] leading-relaxed text-ink-dim">
              {job?.log.slice(-8).join("\n")}
            </pre>
            <button
              onClick={onClose}
              className="mt-6 w-full border border-line px-6 py-3 font-display text-sm uppercase tracking-widest text-ink transition-colors hover:border-ink-dim"
            >
              Back to the desk
            </button>
          </div>
        )}

        {job?.stage === "done" && (
          <p className="mt-6 text-[11px] uppercase tracking-[0.35em]" style={{ color: accent }}>
            Signed. Taking you to the release…
          </p>
        )}
      </div>
    </div>,
    document.body,
  );
}
