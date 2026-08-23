import Link from "next/link";
import Cover from "@/components/Cover";
import SignForm from "@/components/SignForm";
import { getTracks } from "@/lib/data";

export const dynamic = "force-dynamic";

const PIPELINE = [
  {
    n: "01",
    title: "A&R reads the source",
    body: "The label interrogates the repo, Greptile-style — real files, real TODOs, the comment somebody hoped nobody would find.",
  },
  {
    n: "02",
    title: "Claude writes the track",
    body: "The intel becomes verses. Every bar cites an actual file; the hook is usually the thing you should have refactored.",
  },
  {
    n: "03",
    title: "ACE-Step cuts the record",
    body: "ACE-Step 1.5 on a Modal L40S GPU sings it back — about 75 seconds of tape per take.",
  },
  {
    n: "04",
    title: "Mastered & pressed",
    body: "Loudness-normalized, pressed to the roster, streaming on this very page. Signed to DropTable Records.",
  },
];

export default function Home() {
  const tracks = getTracks();

  return (
    <div>
      {/* ---- hero ---- */}
      <section className="grain relative overflow-hidden">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src="/art/herowide.png"
          alt=""
          className="absolute inset-0 h-full w-full object-cover"
          style={{ objectPosition: "right center", filter: "contrast(1.05) saturate(0.8)" }}
        />
        <div
          className="absolute inset-0"
          style={{
            background:
              "linear-gradient(100deg, rgba(13,11,9,0.97) 30%, rgba(13,11,9,0.82) 60%, rgba(13,11,9,0.55)), linear-gradient(to bottom, rgba(13,11,9,0.3), rgba(13,11,9,0.1) 40%, var(--bg) 96%)",
          }}
        />

        <div className="relative z-10 mx-auto max-w-7xl px-5 pb-24 pt-20 sm:pt-28">
          <p className="text-[11px] uppercase tracking-[0.35em] text-ink-dim">
            A record label for codebases
          </p>
          <h1 className="font-display display-tight mt-5 max-w-5xl text-[15vw] text-paper sm:text-[9.5vw] lg:text-[8.2rem]">
            Every repo has a song in it.{" "}
            <span className="block text-[color:var(--accent-phonk)]">We sign them.</span>
          </h1>
          <p className="mt-6 max-w-xl text-base leading-relaxed text-ink-dim sm:text-lg">
            Paste a GitHub repo. Pick a sound. Our A&amp;R reads the source and
            cuts a full track about what it finds — hooks, verses, and the
            skeletons in your <span className="font-mono text-ink">utils/</span> folder.
          </p>

          <div className="mt-12 max-w-2xl">
            <SignForm />
          </div>
        </div>
      </section>

      {/* ---- roster marquee ---- */}
      {tracks.length > 0 && (
        <section className="border-y border-line py-14">
          <div className="mx-auto mb-8 flex max-w-7xl items-baseline justify-between px-5">
            <h2 className="font-display display-tight text-3xl text-paper sm:text-4xl">
              Now on the roster
            </h2>
            <Link
              href="/roster"
              className="text-xs uppercase tracking-[0.25em] text-ink-dim transition-colors hover:text-ink"
            >
              Full roster →
            </Link>
          </div>
          <div className="overflow-hidden">
            <div className="marquee flex w-max gap-5 pl-5">
              {[...tracks, ...tracks].map((t, i) => (
                <Link
                  key={`${t.slug}-${i}`}
                  href={`/track/${t.slug}`}
                  className="block w-60 shrink-0 transition-transform hover:-translate-y-1"
                  aria-hidden={i >= tracks.length}
                  tabIndex={i >= tracks.length ? -1 : undefined}
                >
                  <Cover
                    repo={t.repo}
                    style={t.style}
                    title={t.song_title}
                    artist={t.artist_name}
                  />
                </Link>
              ))}
            </div>
          </div>
        </section>
      )}

      {/* ---- how the label works ---- */}
      <section className="grain relative overflow-hidden">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src="/art/lib1.jpg"
          alt=""
          className="absolute inset-0 h-full w-full object-cover opacity-[0.13]"
          style={{ filter: "grayscale(0.6)" }}
        />
        <div
          className="absolute inset-0"
          style={{
            background: "linear-gradient(var(--bg) 0%, rgba(13,11,9,0.6) 40%, var(--bg) 100%)",
          }}
        />
        <div className="relative z-10 mx-auto max-w-7xl px-5 py-24">
          <p className="text-[11px] uppercase tracking-[0.35em] text-ink-dim">
            How the label works
          </p>
          <h2 className="font-display display-tight mt-4 max-w-3xl text-4xl text-paper sm:text-6xl">
            From clone to chart in one session
          </h2>
          <div className="mt-14 grid gap-10 sm:grid-cols-2 lg:grid-cols-4">
            {PIPELINE.map((s) => (
              <div key={s.n} className="border-t border-line pt-5">
                <span className="font-mono text-xs text-[color:var(--accent-phonk)]">{s.n}</span>
                <h3 className="font-display mt-3 text-xl uppercase tracking-wide text-ink">
                  {s.title}
                </h3>
                <p className="mt-3 text-sm leading-relaxed text-ink-dim">{s.body}</p>
              </div>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
}
