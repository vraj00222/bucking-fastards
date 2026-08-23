"use client";

import { type ReactNode, useEffect, useRef } from "react";

export default function ReleaseVideo({
  videoUrl,
  audioUrl,
  children,
}: {
  videoUrl: string;
  audioUrl: string;
  children?: ReactNode;
}) {
  const videoRef = useRef<HTMLVideoElement>(null);

  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;
    const announce = (playing: boolean) => {
      window.dispatchEvent(
        new CustomEvent("droptable:playback", {
          detail: { audioUrl, playing, currentTime: video.currentTime, duration: video.duration, source: "video" },
        }),
      );
    };
    const pauseForAudioPlayer = (event: Event) => {
      const { detail } = event as CustomEvent<{ audioUrl: string; source?: string }>;
      if (detail.audioUrl === audioUrl && detail.source === "audio" && !video.paused) video.pause();
    };
    const onPlay = () => announce(true);
    const onPause = () => announce(false);
    const onTime = () => announce(!video.paused);
    video.addEventListener("play", onPlay);
    video.addEventListener("pause", onPause);
    video.addEventListener("ended", onPause);
    video.addEventListener("timeupdate", onTime);
    window.addEventListener("droptable:playback", pauseForAudioPlayer);
    return () => {
      video.removeEventListener("play", onPlay);
      video.removeEventListener("pause", onPause);
      video.removeEventListener("ended", onPause);
      video.removeEventListener("timeupdate", onTime);
      window.removeEventListener("droptable:playback", pauseForAudioPlayer);
    };
  }, [audioUrl]);

  return (
    <figure className="relative overflow-hidden border border-line bg-ink shadow-[0_2px_8px_rgba(30,58,158,0.12)]">
      <video ref={videoRef} controls playsInline preload="metadata" className="block aspect-video w-full" src={videoUrl}>
        Your browser does not support the release video.
      </video>
      {children}
      <figcaption className="mono-label border-t border-paper/20 bg-ink px-3 py-2 text-[9px] text-paper/70">
        Original local lyric video · source session visualizer
      </figcaption>
    </figure>
  );
}
