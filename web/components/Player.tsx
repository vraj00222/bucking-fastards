"use client";

import { useEffect, useRef, useState } from "react";
import WaveSurfer from "wavesurfer.js";

function fmt(s: number) {
  return `${Math.floor(s / 60)}:${String(Math.floor(s % 60)).padStart(2, "0")}`;
}

export default function Player({ audioUrl, accent }: { audioUrl: string; accent: string }) {
  const containerRef = useRef<HTMLDivElement>(null);
  const wsRef = useRef<WaveSurfer | null>(null);
  const [playing, setPlaying] = useState(false);
  const [ready, setReady] = useState(false);
  const [time, setTime] = useState(0);
  const [duration, setDuration] = useState(0);

  useEffect(() => {
    if (!containerRef.current) return;
    const ws = WaveSurfer.create({
      container: containerRef.current,
      url: audioUrl,
      height: 64,
      waveColor: "rgba(236,227,210,0.22)",
      progressColor: accent,
      cursorColor: "transparent",
      barWidth: 2,
      barGap: 2,
      barRadius: 2,
      normalize: true,
    });
    wsRef.current = ws;
    ws.on("ready", () => setReady(true));
    ws.on("play", () => setPlaying(true));
    ws.on("pause", () => setPlaying(false));
    ws.on("finish", () => setPlaying(false));
    ws.on("timeupdate", setTime);
    ws.on("decode", setDuration);
    return () => {
      wsRef.current = null;
      try {
        ws.destroy();
      } catch {
        /* wavesurfer aborts in-flight fetch on destroy */
      }
    };
  }, [audioUrl, accent]);

  return (
    <div className="flex items-center gap-5 border border-line bg-bg-raised/60 p-4">
      {/* vinyl: spins at 33 1/3 while the track plays */}
      <div
        aria-hidden
        className="vinyl-spin relative hidden h-16 w-16 shrink-0 rounded-full sm:block"
        style={{
          background:
            "repeating-radial-gradient(circle at 50% 50%, #14100c 0px, #14100c 2px, #221b13 3px, #14100c 4px)",
          boxShadow: "0 0 0 1px var(--line), inset 0 0 18px rgba(0,0,0,0.7)",
          animationPlayState: playing ? "running" : "paused",
        }}
      >
        <div className="absolute inset-0 m-auto h-6 w-6 rounded-full" style={{ background: accent }} />
        <div className="absolute inset-0 m-auto h-1.5 w-1.5 rounded-full bg-bg" />
      </div>

      <button
        type="button"
        onClick={() => wsRef.current?.playPause()}
        disabled={!ready}
        aria-label={playing ? "Pause" : "Play"}
        className="grid h-14 w-14 shrink-0 cursor-pointer place-items-center rounded-full border-2 transition-opacity focus-visible:outline-2 focus-visible:outline-offset-2 disabled:cursor-wait disabled:opacity-40"
        style={{ borderColor: accent, color: accent, outlineColor: accent }}
      >
        {playing ? (
          <svg width="18" height="18" viewBox="0 0 18 18" fill="currentColor" aria-hidden>
            <rect x="3" y="2" width="4" height="14" />
            <rect x="11" y="2" width="4" height="14" />
          </svg>
        ) : (
          <svg width="18" height="18" viewBox="0 0 18 18" fill="currentColor" aria-hidden>
            <path d="M4 2l12 7-12 7z" />
          </svg>
        )}
      </button>

      <div className="min-w-0 flex-1">
        <div ref={containerRef} />
        <div className="mt-2 flex justify-between font-mono text-[11px] text-ink-dim">
          <span>{fmt(time)}</span>
          <span>{ready ? fmt(duration) : "cutting the wax…"}</span>
        </div>
      </div>
    </div>
  );
}
