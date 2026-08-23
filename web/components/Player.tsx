"use client";

import { useEffect, useRef, useState } from "react";
import WaveSurfer from "wavesurfer.js";

function fmt(s: number) {
  return `${Math.floor(s / 60)}:${String(Math.floor(s % 60)).padStart(2, "0")}`;
}

// accent stays in the contract; the player itself keeps to house colors
// (cobalt wave, gold progress) so every pressing looks label-consistent.
export default function Player({ audioUrl }: { audioUrl: string; accent?: string }) {
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
      waveColor: "rgba(30,58,158,0.30)", // cobalt
      progressColor: "#c3941d", // gold
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
  }, [audioUrl]);

  return (
    <div
      className="flex items-center gap-5 border border-line bg-card p-4"
      style={{ boxShadow: "0 2px 8px rgba(30,58,158,0.12)" }}
    >
      {/* vinyl: cobalt grooves, gold label; spins at 33 1/3 while the track plays */}
      <div
        aria-hidden
        className="vinyl-disc vinyl-spin relative hidden h-16 w-16 shrink-0 sm:block"
        style={{
          boxShadow: "0 0 0 1px var(--line)",
          animationPlayState: playing ? "running" : "paused",
        }}
      >
        <div className="absolute inset-0 m-auto h-1.5 w-1.5 rounded-full bg-card" />
      </div>

      <button
        type="button"
        onClick={() => wsRef.current?.playPause()}
        disabled={!ready}
        aria-label={playing ? "Pause" : "Play"}
        className="grid h-14 w-14 shrink-0 cursor-pointer place-items-center rounded-full bg-ink text-paper transition-opacity focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-cobalt disabled:cursor-wait disabled:opacity-40"
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
        <div className="mono-label mt-2 flex justify-between text-[10px] text-ink-dim">
          <span>{fmt(time)}</span>
          <span>{ready ? fmt(duration) : "cutting the wax…"}</span>
        </div>
      </div>
    </div>
  );
}
