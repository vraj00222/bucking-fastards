"use client";

import { useState } from "react";
import { PRESETS, type StyleId } from "@/lib/presets";
import Theater from "@/components/Theater";

const STYLES = Object.keys(PRESETS) as StyleId[];

export default function SignForm() {
  const [repo, setRepo] = useState("");
  const [style, setStyle] = useState<StyleId>("phonk");
  const [jobId, setJobId] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const accent = PRESETS[style].accent;

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      const r = await fetch("/api/sign", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ repo, style }),
      });
      const j = await r.json();
      if (!r.ok) {
        setError(j.error ?? "Something broke at the label. Try again.");
      } else {
        setJobId(j.job);
      }
    } catch {
      setError("Couldn't reach the label. Is the server up?");
    } finally {
      setBusy(false);
    }
  };

  return (
    <form onSubmit={submit} style={{ "--accent": accent } as React.CSSProperties}>
      <label htmlFor="repo" className="mono-label block text-[11px] text-ink-dim">
        The repo or pull request
      </label>
      <input
        id="repo"
        type="text"
        required
        value={repo}
        onChange={(e) => setRepo(e.target.value)}
        placeholder="github.com/owner/repo or /pull/123"
        autoComplete="off"
        spellCheck={false}
        className="mt-2 w-full border border-line bg-paper px-3 py-3 font-mono text-lg text-ink outline-none transition-[border-color,box-shadow] placeholder:text-ink-dim/50 focus:border-cobalt focus:ring-2 focus:ring-cobalt/25"
      />

      <p className="mono-label mt-8 text-[11px] text-ink-dim">The sound</p>
      <div className="mt-3 grid grid-cols-3 gap-2 sm:grid-cols-5">
        {STYLES.map((s) => {
          const p = PRESETS[s];
          const selected = s === style;
          return (
            <button
              key={s}
              type="button"
              onClick={() => setStyle(s)}
              aria-pressed={selected}
              className={`relative aspect-[5/4] overflow-hidden bg-card p-1.5 text-left transition-all focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-cobalt ${
                selected
                  ? "tilt-l border-2 border-gold"
                  : "border border-line opacity-75 hover:border-cobalt hover:opacity-100"
              }`}
              style={
                selected ? { boxShadow: "0 2px 8px rgba(30,58,158,0.12)" } : undefined
              }
            >
              {/* mini album plate: accent art field */}
              <span
                className="block h-[55%] w-full border"
                style={{
                  background: p.accent,
                  borderColor: "color-mix(in srgb, var(--ink) 25%, transparent)",
                }}
              />
              <span
                className="font-display absolute bottom-1.5 left-1.5 right-1.5 text-[11px] uppercase leading-none tracking-wide"
                style={{ color: selected ? p.accent : "var(--ink)" }}
              >
                {s}
              </span>
            </button>
          );
        })}
      </div>
      <p className="mt-3 min-h-4 text-xs italic text-ink-dim">{PRESETS[style].caption}</p>

      <button
        type="submit"
        disabled={busy}
        className="mt-8 w-full px-8 py-4 font-display text-xl uppercase tracking-widest text-paper transition-[filter] hover:brightness-110 disabled:opacity-60 sm:w-auto"
        style={{ background: accent, boxShadow: "0 2px 8px rgba(30,58,158,0.12)" }}
      >
        Sign this repo or PR
      </button>
      {error && <p className="mt-3 text-sm text-[color:var(--accent)]">{error}</p>}

      {jobId && (
        <Theater jobId={jobId} style={style} repo={repo} onClose={() => setJobId(null)} />
      )}
    </form>
  );
}
