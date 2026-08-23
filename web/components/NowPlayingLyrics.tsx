"use client";

import { useEffect, useMemo, useState } from "react";

type Playback = {
  playing: boolean;
  currentTime: number;
  duration: number;
};

type LyricLine = {
  text: string;
  section: string;
};

function lyricLines(lyrics: string): LyricLine[] {
  let section = "now playing";
  return lyrics.split("\n").flatMap((line) => {
    const tag = line.match(/^\s*\[(.+)\]\s*$/);
    if (tag) {
      section = tag[1];
      return [];
    }
    return line.trim() ? [{ text: line.trim(), section }] : [];
  });
}

export default function NowPlayingLyrics({
  lyrics,
  audioUrl,
}: {
  lyrics: string;
  audioUrl: string;
}) {
  const lines = useMemo(() => lyricLines(lyrics), [lyrics]);
  const [playback, setPlayback] = useState<Playback>({
    playing: false,
    currentTime: 0,
    duration: 0,
  });

  useEffect(() => {
    const onPlayback = (event: Event) => {
      const { detail } = event as CustomEvent<Playback & { audioUrl: string }>;
      if (detail.audioUrl === audioUrl) setPlayback(detail);
    };
    window.addEventListener("droptable:playback", onPlayback);
    return () => window.removeEventListener("droptable:playback", onPlayback);
  }, [audioUrl]);

  if (!lines.length) return null;
  const index = playback.duration
    ? Math.min(lines.length - 1, Math.floor((playback.currentTime / playback.duration) * lines.length))
    : 0;
  const line = lines[index];

  return (
    <aside
      aria-live="polite"
      aria-atomic="true"
      aria-hidden={!playback.playing}
      className={`pointer-events-none absolute top-[15%] right-[4%] z-20 w-[58%] border-l-2 border-gold bg-cobalt px-3 py-3 text-paper shadow-[0_8px_20px_rgba(22,19,14,0.28)] transition-all duration-150 sm:px-4 sm:py-4 ${
        playback.playing ? "translate-x-0 opacity-100" : "translate-x-3 opacity-0"
      }`}
    >
      <p className="mono-label text-[7px] text-gold sm:text-[8px]">{line.section}</p>
      <p key={index} className="now-playing-lyric mt-2 text-[11px] leading-[1.35] sm:text-sm">
        {line.text}
      </p>
      <div className="mt-3 h-px w-8 bg-gold/70" />
    </aside>
  );
}
