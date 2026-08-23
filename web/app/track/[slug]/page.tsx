import type { Metadata } from "next";
import { notFound } from "next/navigation";
import Cover from "@/components/Cover";
import Lyrics from "@/components/Lyrics";
import NowPlayingLyrics from "@/components/NowPlayingLyrics";
import Player from "@/components/Player";
import ReleaseVideo from "@/components/ReleaseVideo";
import { getTrack, getTracks } from "@/lib/data";
import { presetFor } from "@/lib/presets";

// New tracks land in ../data/tracks.json without a rebuild.
export const dynamic = "force-dynamic";

const compact = new Intl.NumberFormat("en", { notation: "compact" });

export async function generateMetadata({
  params,
}: {
  params: Promise<{ slug: string }>;
}): Promise<Metadata> {
  const track = getTrack(decodeURIComponent((await params).slug));
  return track
    ? { title: `${track.song_title} — ${track.artist_name} | DropTable Records` }
    : {};
}

export default async function TrackPage({ params }: { params: Promise<{ slug: string }> }) {
  const slug = decodeURIComponent((await params).slug);
  const tracks = getTracks();
  const track = tracks.find((t) => t.slug === slug);
  if (!track) notFound();
  const { accent } = presetFor(track.style);
  const catalogNo = `DTR-${String(tracks.indexOf(track) + 1).padStart(3, "0")}`;

  // Accent lands on the last word of the title; ink carries the rest.
  const words = track.song_title.split(" ");
  const lastWord = words.pop();

  const chip =
    "mono-label inline-flex items-center gap-1.5 border px-3 py-1.5 text-[10px] text-cobalt border-cobalt/40";

  return (
    <div className="mx-auto max-w-7xl px-5 py-10 lg:py-16">
      {/* hero: engraved plate left, credits + player right */}
      <div className="grid gap-10 lg:grid-cols-[minmax(0,440px)_1fr] lg:gap-14">
        <div className="relative mx-auto w-full max-w-md lg:mx-0 lg:max-w-none">
          <Cover
            repo={track.repo}
            style={track.style}
            title={track.song_title}
            artist={track.artist_name}
            size="lg"
          />
          {!track.video_url && <NowPlayingLyrics lyrics={track.lyrics} audioUrl={track.audio_url} />}
        </div>

        <div className="flex min-w-0 flex-col gap-5">
          <div className="flex flex-wrap items-center gap-3">
            {/* gold-outlined label seal */}
            <p className="mono-label tilt-l inline-flex items-center gap-2 border-2 border-gold px-3 py-1.5 text-[10px] text-ink">
              <span className="h-1.5 w-1.5 rounded-full bg-gold" />
              Signed to DropTable Records
            </p>
            <span className="mono-label text-[10px] text-ink-dim">{catalogNo}</span>
          </div>

          <div>
            <h1 className="font-display display-tight break-words text-[clamp(2.75rem,6.5vw,6rem)] text-ink">
              {words.length > 0 && <>{words.join(" ")} </>}
              <span style={{ color: accent }}>{lastWord}</span>
            </h1>
            <p className="mono-label mt-3 text-xs text-ink-dim">{track.artist_name}</p>
          </div>

          <p className="max-w-xl text-sm leading-6 text-ink-dim">{track.description}</p>

          {/* catalog tags */}
          <div className="flex flex-wrap gap-2">
            <span className={chip} style={{ color: accent, borderColor: accent }}>
              {track.style}
            </span>
            <a
              href={`https://github.com/${track.repo}`}
              target="_blank"
              rel="noopener noreferrer"
              className={`${chip} transition-colors hover:text-cobalt-hover`}
            >
              {track.repo} ↗
            </a>
            <span className={chip}>★ {compact.format(track.stars)}</span>
            <span className={chip}>{track.language}</span>
          </div>

          <Player audioUrl={track.audio_url} accent={accent} />

          {track.video_url && (
            <ReleaseVideo videoUrl={track.video_url} audioUrl={track.audio_url}>
              <NowPlayingLyrics lyrics={track.lyrics} audioUrl={track.audio_url} />
            </ReleaseVideo>
          )}

          <div className="flex flex-wrap items-baseline justify-between gap-3">
            <a
              href={track.audio_url}
              download
              className="mono-label border border-cobalt px-4 py-2 text-[10px] text-cobalt transition-colors hover:bg-cobalt hover:text-paper"
            >
              Download the single ↓
            </a>
            {track.timing && (
              <p className="mono-label text-[10px] text-ink-dim">
                Mined {track.timing.intel_s}s · Written {track.timing.lyrics_s}s · Recorded{" "}
                {track.timing.audio_s}s{track.timing.video_s ? ` · Cut ${track.timing.video_s}s` : ""}
              </p>
            )}
          </div>
        </div>
      </div>

      {/* liner notes; blue angel plate rests along the right margin on wide screens */}
      <section className="rule-double relative mt-16 overflow-hidden pt-10 lg:mt-24">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src="/art/long2.jpg"
          alt=""
          aria-hidden
          className="pointer-events-none absolute right-0 top-10 hidden h-[calc(100%-2.5rem)] w-1/4 object-cover object-top xl:block"
          style={{
            opacity: 0.4,
            maskImage: "linear-gradient(to left, black 55%, transparent)",
          }}
        />
        <h2 className="font-display display-tight text-2xl text-ink">
          Liner notes<span style={{ color: accent }}>;</span>
        </h2>
        <p className="mono-label mt-1 mb-8 text-[10px] text-ink-dim">
          Underlined lines were mined from the repo
        </p>
        <Lyrics
          lyrics={track.lyrics}
          facts={track.facts_highlights}
          audioUrl={track.audio_url}
          accent={accent}
        />
      </section>
    </div>
  );
}
