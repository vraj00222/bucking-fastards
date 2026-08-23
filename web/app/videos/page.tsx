import Link from "next/link";
import { getTracks } from "@/lib/data";

export const dynamic = "force-dynamic";
export const metadata = { title: "Video Gallery — DropTable Records" };

export default function VideosPage() {
  const tracks = getTracks().filter((track) => track.video_url).slice().reverse();
  return (
    <div className="mx-auto max-w-7xl px-5 py-14 sm:py-20">
      <p className="mono-label text-[11px] text-cobalt">DropTable screen tests</p>
      <h1 className="font-display display-tight mt-4 max-w-4xl text-6xl text-ink sm:text-8xl">Video gallery</h1>
      <p className="mt-5 max-w-2xl text-sm leading-6 text-ink-dim">
        Original local lyric videos cut from each signed release — generated song, source-session visuals, and timed words in one take.
      </p>
      <div className="rule-double mt-10" />
      {tracks.length ? (
        <div className="mt-10 grid gap-10 md:grid-cols-2">
          {tracks.map((track) => (
            <article key={track.slug} className="group">
              <Link href={`/track/${track.slug}`} className="block overflow-hidden border border-line bg-ink">
                <video muted playsInline preload="metadata" className="block aspect-video w-full transition-transform duration-500 group-hover:scale-[1.015]" src={track.video_url!} />
              </Link>
              <div className="mt-4 flex items-baseline justify-between gap-5">
                <div>
                  <p className="mono-label text-[10px] text-cobalt">{track.repo}</p>
                  <h2 className="font-display display-tight mt-1 text-2xl text-ink">{track.song_title}</h2>
                  <p className="text-sm text-ink-dim">{track.artist_name}</p>
                </div>
                <Link href={`/track/${track.slug}`} className="mono-label shrink-0 text-[10px] text-cobalt hover:text-cobalt-hover">
                  Watch / play →
                </Link>
              </div>
            </article>
          ))}
        </div>
      ) : (
        <p className="mt-14 text-ink-dim">No visual releases yet. Sign a repository to cut the first one.</p>
      )}
    </div>
  );
}
