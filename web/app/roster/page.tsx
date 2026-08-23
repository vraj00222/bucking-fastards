import Link from "next/link";
import Cover from "@/components/Cover";
import { getTracks, type Track } from "@/lib/data";
import { presetFor } from "@/lib/presets";

export const dynamic = "force-dynamic";

export const metadata = { title: "The Roster — DropTable Records" };

function ReleaseCard({ track, showArtist = true }: { track: Track; showArtist?: boolean }) {
  const { accent } = presetFor(track.style);
  return (
    <Link href={`/track/${track.slug}`} className="group block">
      <div className="relative">
        {/* accent glow on hover */}
        <div
          aria-hidden
          className="absolute -inset-3 opacity-0 blur-2xl transition-opacity duration-300 group-hover:opacity-30"
          style={{ background: accent }}
        />
        {/* vinyl peek: record slides out from behind the sleeve */}
        <div
          aria-hidden
          className="absolute inset-[3%] rounded-full transition-transform duration-300 ease-out group-hover:translate-x-[13%] group-hover:rotate-12"
          style={{
            background: `radial-gradient(circle, ${accent} 0 17%, #0a0806 17.5% 20%, transparent 20.5%), repeating-radial-gradient(circle, #1b1712 0 2px, #0a0806 2px 5px)`,
            boxShadow: "4px 0 14px rgba(0,0,0,0.6)",
          }}
        />
        <div className="relative transition-transform duration-300 ease-out group-hover:-translate-y-1.5">
          <Cover repo={track.repo} style={track.style} title={track.song_title} artist={track.artist_name} size="sm" />
        </div>
      </div>

      <div className="relative z-10 mt-4">
        {showArtist && (
          <p className="font-display display-tight text-lg text-ink group-hover:text-paper transition-colors">
            {track.artist_name}
          </p>
        )}
        <p className={`text-sm text-ink-dim ${showArtist ? "mt-0.5" : "font-display display-tight text-lg text-ink group-hover:text-paper transition-colors"}`}>
          {track.song_title}
        </p>
        <div className="mt-2 flex items-center gap-3">
          <span
            className="border px-1.5 py-0.5 text-[10px] uppercase tracking-[0.2em]"
            style={{ color: accent, borderColor: accent }}
          >
            {track.style}
          </span>
          <span className="truncate font-mono text-[11px] text-ink-dim">{track.repo}</span>
        </div>
      </div>
    </Link>
  );
}

export default function RosterPage() {
  // tracks.json is append-only; reverse so the newest signing leads.
  const tracks = getTracks().slice().reverse();

  // Group by repo, keeping newest-first order of first appearance.
  const groups: { repo: string; tracks: Track[] }[] = [];
  const byRepo = new Map<string, Track[]>();
  for (const t of tracks) {
    let g = byRepo.get(t.repo);
    if (!g) {
      g = [];
      byRepo.set(t.repo, g);
      groups.push({ repo: t.repo, tracks: g });
    }
    g.push(t);
  }

  return (
    <div>
      {/* header band: reading-room fresco under heavy dark scrim */}
      <section className="grain relative overflow-hidden border-b border-line">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src="/art/bg3.jpg"
          alt=""
          className="absolute inset-0 h-full w-full object-cover object-center"
          style={{ filter: "grayscale(1) contrast(1.1)", opacity: 0.28 }}
        />
        <div
          className="absolute inset-0"
          style={{ background: "linear-gradient(to bottom, rgba(13,11,9,0.55), rgba(13,11,9,0.92))" }}
        />
        <div className="relative z-10 mx-auto max-w-7xl px-5 pb-14 pt-20">
          <p className="text-xs uppercase tracking-[0.35em] text-ink-dim">Label discography</p>
          <h1 className="font-display display-tight mt-3 text-[18vw] leading-none text-paper sm:text-8xl md:text-9xl">
            The Roster
          </h1>
          <div className="mt-6 flex flex-wrap items-baseline gap-x-8 gap-y-2">
            <p className="text-sm uppercase tracking-[0.2em] text-ink">
              {groups.length} {groups.length === 1 ? "artist" : "artists"} signed
              <span className="text-ink-dim"> · {tracks.length} {tracks.length === 1 ? "release" : "releases"}</span>
            </p>
            <p className="text-sm text-ink-dim">The label remembers every artist.</p>
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-7xl px-5 py-14">
        {tracks.length === 0 ? (
          <div className="flex flex-col items-start gap-6 py-20">
            <p className="font-display display-tight text-5xl text-ink sm:text-7xl">
              No artists signed yet.
            </p>
            <p className="text-ink-dim">Be the first A&amp;R.</p>
            <Link
              href="/sign"
              className="border border-ink px-6 py-3 text-xs uppercase tracking-[0.3em] text-ink transition-colors hover:bg-ink hover:text-bg"
            >
              Sign a repo
            </Link>
          </div>
        ) : (
          <div className="grid grid-cols-2 gap-x-6 gap-y-12 sm:grid-cols-3 lg:grid-cols-4">
            {groups.map((g) =>
              g.tracks.length === 1 ? (
                <ReleaseCard key={g.tracks[0].slug} track={g.tracks[0]} />
              ) : (
                // an artist with multiple releases gets a full-width discography row
                <div key={g.repo} className="col-span-full border-t border-line pt-8">
                  <div className="mb-6 flex flex-wrap items-baseline gap-x-6 gap-y-1">
                    <h2 className="font-display display-tight text-3xl text-paper sm:text-4xl">
                      {g.tracks[0].artist_name}
                    </h2>
                    <p className="text-[11px] uppercase tracking-[0.3em] text-ink-dim">
                      Discography · {g.tracks.length} releases
                    </p>
                    <p className="font-mono text-[11px] text-ink-dim">{g.repo}</p>
                  </div>
                  <div className="grid grid-cols-2 gap-x-6 gap-y-10 sm:grid-cols-3 lg:grid-cols-4">
                    {g.tracks.map((t) => (
                      <ReleaseCard key={t.slug} track={t} showArtist={false} />
                    ))}
                  </div>
                </div>
              )
            )}
          </div>
        )}
      </section>
    </div>
  );
}
