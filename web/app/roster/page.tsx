import Link from "next/link";
import Cover from "@/components/Cover";
import { getTracks, type Track } from "@/lib/data";
import { presetFor } from "@/lib/presets";

export const dynamic = "force-dynamic";

export const metadata = { title: "The Roster — DropTable Records" };

function ReleaseCard({
  track,
  catalog,
  showArtist = true,
}: {
  track: Track;
  catalog: string;
  showArtist?: boolean;
}) {
  const { accent } = presetFor(track.style);
  return (
    <Link href={`/track/${track.slug}`} className="group block">
      <div className="relative">
        {/* vinyl peek: cobalt grooved disc slides out from behind the plate */}
        <div
          aria-hidden
          className="vinyl-disc absolute inset-[3%] transition-transform duration-300 ease-out group-hover:translate-x-[13%] group-hover:rotate-12"
          style={{ boxShadow: "0 2px 8px rgba(30,58,158,0.12)" }}
        />
        <div className="relative transition-transform duration-300 ease-out group-hover:-translate-y-1.5">
          <Cover repo={track.repo} style={track.style} title={track.song_title} artist={track.artist_name} size="sm" />
        </div>
      </div>

      <div className="relative z-10 mt-4">
        <p className="mono-label text-[10px] text-cobalt">{catalog}</p>
        {showArtist && (
          <p className="font-display display-tight mt-1 text-lg text-ink transition-colors group-hover:text-cobalt">
            {track.artist_name}
          </p>
        )}
        <p className={`text-sm text-ink-dim ${showArtist ? "mt-0.5" : "font-display display-tight mt-1 text-lg text-ink transition-colors group-hover:text-cobalt"}`}>
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
  // tracks.json is append-only; catalog numbers follow signing order.
  const all = getTracks();
  const catalogOf = new Map(all.map((t, i) => [t.slug, `DTR-${String(i + 1).padStart(3, "0")}`]));
  // Reverse so the newest signing leads.
  const tracks = all.slice().reverse();

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
      {/* header: catalog-card masthead with the blue angel as side art */}
      <section className="grain relative overflow-hidden border-b border-line bg-paper">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src="/art/long2.jpg"
          alt=""
          aria-hidden
          className="absolute inset-y-0 right-0 hidden h-full w-[36%] object-cover object-top md:block"
          style={{
            maskImage: "linear-gradient(to right, transparent, black 30%)",
            WebkitMaskImage: "linear-gradient(to right, transparent, black 30%)",
          }}
        />
        <div className="relative z-10 mx-auto max-w-7xl px-5 pb-12 pt-20">
          <p className="mono-label text-[11px] text-ink-dim">Label discography</p>
          <h1 className="font-display display-tight mt-3 text-[18vw] leading-none text-ink sm:text-8xl md:text-9xl">
            The Roster
          </h1>
          <div className="rule-double mt-6 max-w-2xl" />
          <div className="mt-4 flex flex-wrap items-baseline gap-x-8 gap-y-2">
            <p className="mono-label text-[11px] text-ink">
              Artists on file: {groups.length}
              <span className="text-ink-dim"> · Releases: {tracks.length}</span>
            </p>
            <p className="text-sm text-ink-dim">The label remembers every artist.</p>
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-7xl px-5 py-14">
        {tracks.length === 0 ? (
          <div className="flex flex-col items-start gap-6 py-20">
            <div aria-hidden className="vinyl-disc tilt-l h-28 w-28" />
            <p className="font-display display-tight text-5xl text-ink sm:text-7xl">
              No artists signed yet.
            </p>
            <p className="text-ink-dim">Be the first A&amp;R.</p>
            <Link
              href="/#sign"
              className="border border-ink px-6 py-3 text-xs uppercase tracking-[0.3em] text-ink transition-colors hover:bg-ink hover:text-paper"
            >
              Sing a repo
            </Link>
          </div>
        ) : (
          <div className="grid grid-cols-2 gap-x-6 gap-y-12 sm:grid-cols-3 lg:grid-cols-4">
            {groups.map((g) =>
              g.tracks.length === 1 ? (
                <ReleaseCard
                  key={g.tracks[0].slug}
                  track={g.tracks[0]}
                  catalog={catalogOf.get(g.tracks[0].slug)!}
                />
              ) : (
                // an artist with multiple releases gets a full-width catalog-card row
                <div key={g.repo} className="rule-line col-span-full pt-8">
                  <div className="mb-6 flex flex-wrap items-baseline gap-x-6 gap-y-2">
                    <h2 className="font-display display-tight text-3xl text-ink sm:text-4xl">
                      {g.tracks[0].artist_name}
                    </h2>
                    <p className="mono-label text-[11px] text-ink-dim">
                      Discography · {g.tracks.length} releases
                    </p>
                    <p className="font-mono text-[11px] text-ink-dim">{g.repo}</p>
                    <span className="mono-label tilt-r border border-gold px-2 py-1 text-[10px] text-gold">
                      The difficult second album
                    </span>
                  </div>
                  <div className="grid grid-cols-2 gap-x-6 gap-y-10 sm:grid-cols-3 lg:grid-cols-4">
                    {g.tracks.map((t) => (
                      <ReleaseCard key={t.slug} track={t} catalog={catalogOf.get(t.slug)!} showArtist={false} />
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
