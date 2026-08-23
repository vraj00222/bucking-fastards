import type { Metadata } from "next";
import { notFound } from "next/navigation";
import Cover from "@/components/Cover";
import Lyrics from "@/components/Lyrics";
import Player from "@/components/Player";
import { artForRepo } from "@/lib/art";
import { getTrack } from "@/lib/data";
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
  const track = getTrack(decodeURIComponent((await params).slug));
  if (!track) notFound();
  const { accent } = presetFor(track.style);

  const chip =
    "inline-flex items-center gap-1.5 border border-line px-3 py-1.5 text-[11px] uppercase tracking-[0.15em] text-ink-dim";

  return (
    <div className="mx-auto max-w-7xl px-5 py-10 lg:py-16">
      {/* hero: sleeve left, credits + player right */}
      <div className="grid gap-10 lg:grid-cols-[minmax(0,440px)_1fr] lg:gap-14">
        <div className="mx-auto w-full max-w-md lg:mx-0 lg:max-w-none">
          <Cover
            repo={track.repo}
            style={track.style}
            title={track.song_title}
            artist={track.artist_name}
            size="lg"
          />
        </div>

        <div className="flex min-w-0 flex-col gap-5">
          <p className="inline-flex items-center gap-2 self-start border border-line px-3 py-1.5 text-[11px] uppercase tracking-[0.25em] text-ink-dim">
            <span className="h-1.5 w-1.5 rounded-full" style={{ background: accent }} />
            Signed to DropTable Records
          </p>

          <div>
            <h1 className="font-display display-tight break-words text-[clamp(2.75rem,6.5vw,6rem)] text-ink">
              {track.song_title}
            </h1>
            <p className="mt-3 text-sm uppercase tracking-[0.3em]" style={{ color: accent }}>
              {track.artist_name}
            </p>
          </div>

          <p className="max-w-xl text-sm leading-6 text-ink-dim">{track.description}</p>

          <div className="flex flex-wrap gap-2">
            <span className={chip} style={{ color: accent, borderColor: accent }}>
              {track.style}
            </span>
            <a
              href={`https://github.com/${track.repo}`}
              target="_blank"
              rel="noopener noreferrer"
              className={`${chip} transition-colors hover:text-ink`}
            >
              {track.repo} ↗
            </a>
            <span className={chip}>★ {compact.format(track.stars)}</span>
            <span className={chip}>{track.language}</span>
          </div>

          <Player audioUrl={track.audio_url} accent={accent} />

          <div className="flex flex-wrap items-baseline justify-between gap-3">
            <a
              href={track.audio_url}
              download
              className="border border-line px-4 py-2 text-[11px] uppercase tracking-[0.2em] text-ink transition-colors hover:bg-bg-raised"
            >
              Download the single ↓
            </a>
            {track.timing && (
              <p className="font-mono text-[11px] text-ink-dim">
                mined in {track.timing.intel_s}s · written in {track.timing.lyrics_s}s · recorded
                in {track.timing.audio_s}s
              </p>
            )}
          </div>
        </div>
      </div>

      {/* liner notes over a faint pressing of the sleeve art */}
      <section className="relative mt-16 overflow-hidden border-t border-line pt-10 lg:mt-24">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src={artForRepo(track.repo)}
          alt=""
          aria-hidden
          className="pointer-events-none absolute -right-10 top-0 hidden h-full w-1/2 object-cover lg:block"
          style={{
            filter: "grayscale(1)",
            opacity: 0.07,
            maskImage: "linear-gradient(to left, black 40%, transparent)",
          }}
        />
        <h2 className="font-display display-tight text-2xl text-ink">
          Liner notes<span style={{ color: accent }}>;</span>
        </h2>
        <p className="mt-1 mb-8 text-[11px] uppercase tracking-[0.25em] text-ink-dim">
          Underlined lines were mined from the repo
        </p>
        <Lyrics lyrics={track.lyrics} facts={track.facts_highlights} accent={accent} />
      </section>
    </div>
  );
}
