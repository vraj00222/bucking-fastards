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
      <label htmlFor="repo" className="block text-[11px] uppercase tracking-[0.3em] text-ink-dim">
        The artist
      </label>
      <input
        id="repo"
        type="text"
        required
        value={repo}
        onChange={(e) => setRepo(e.target.value)}
        placeholder="github.com/owner/repo"
        autoComplete="off"
        spellCheck={false}
        className="mt-2 w-full border-0 border-b-2 border-line bg-transparent py-3 font-mono text-lg text-ink outline-none transition-colors placeholder:text-ink-dim/50 focus:border-[var(--accent)]"
      />

      <p className="mt-8 text-[11px] uppercase tracking-[0.3em] text-ink-dim">The sound</p>
      <div className="mt-3 grid grid-cols-2 gap-2 sm:grid-cols-5">
        {STYLES.map((s) => {
          const p = PRESETS[s];
          const selected = s === style;
          return (
            <button
              key={s}
              type="button"
              onClick={() => setStyle(s)}
              aria-pressed={selected}
              className="grain relative aspect-[5/4] overflow-hidden border text-left transition-all focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-paper"
              style={{
                background: `linear-gradient(150deg, ${p.accent} -30%, ${p.accent}44 35%, #14100c 95%)`,
                borderColor: selected ? "var(--paper)" : "var(--line)",
                opacity: selected ? 1 : 0.65,
              }}
            >
              <span
                className="absolute left-2 top-2 h-1.5 w-1.5 rounded-full"
                style={{ background: p.accent }}
              />
              <span className="absolute bottom-2 left-2 right-2 font-display text-sm uppercase leading-none tracking-wide text-paper">
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
        className="mt-8 w-full px-8 py-4 font-display text-xl uppercase tracking-widest text-black transition-[filter] hover:brightness-110 disabled:opacity-60 sm:w-auto"
        style={{ background: accent }}
      >
        🎤 Sign this repo
      </button>
      {error && <p className="mt-3 text-sm text-[color:var(--accent)]">{error}</p>}

      {jobId && (
        <Theater jobId={jobId} style={style} repo={repo} onClose={() => setJobId(null)} />
      )}
    </form>
  );
}
