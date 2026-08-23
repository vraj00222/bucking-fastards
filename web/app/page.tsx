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
      {/* ---- hero: paper ground, ink poster type, the statue plate ---- */}
      <section className="grain relative overflow-hidden">
        <div className="mx-auto grid max-w-7xl items-end gap-10 px-5 pt-16 sm:pt-20 lg:grid-cols-[minmax(0,1fr)_minmax(280px,34%)]">
          <div className="pb-16 sm:pb-20">
            <p className="mono-label text-[11px] text-cobalt">
              A record label for codebases
            </p>
            <h1 className="font-display display-tight mt-6 max-w-4xl text-[14vw] text-ink sm:text-[9vw] lg:text-[7.2rem]">
              Every repo has a song in it.{" "}
              <span className="block">
                We{" "}
                <em
                  style={{
                    fontFamily: "Georgia, 'Times New Roman', serif",
                    fontStyle: "italic",
                    fontWeight: 500,
                    textTransform: "none",
                    letterSpacing: "-0.02em",
                    fontSize: "0.94em",
                    color: "var(--cobalt)",
                  }}
                >
                  sign
                </em>{" "}
                them.
              </span>
            </h1>
            <p className="mt-6 max-w-xl text-base leading-relaxed text-ink-dim sm:text-lg">
              Paste a GitHub repo. Pick a sound. Our A&amp;R reads the source and
              cuts a full track about what it finds — hooks, verses, and the
              skeletons in your <span className="font-mono text-ink">utils/</span> folder.
            </p>

            {/* intake form as a catalog card */}
            <div
              id="sign"
              className="mt-10 max-w-2xl scroll-mt-24 border border-line bg-card p-6 sm:p-8"
              style={{ boxShadow: "0 2px 8px rgba(30,58,158,0.12)" }}
            >
              <div className="rule-double mb-6 flex items-baseline justify-between pt-2">
                <span className="mono-label text-[10px] text-ink-dim">
                  A&amp;R intake
                </span>
                <span className="mono-label text-[10px] text-gold">Form DTR/1</span>
              </div>
              <SignForm />
            </div>
          </div>

          {/* the head of A&R: blue engraved statue, gold sunglasses, smoothie.
              White-ground plate, hairline cobalt frame, cropped at the shelf. */}
          <div className="hidden self-end lg:block">
            <div
              className="tilt-r overflow-hidden border border-cobalt bg-white p-2 pb-0"
              style={{ boxShadow: "0 2px 8px rgba(30,58,158,0.12)" }}
            >
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src="/art/long.jpg"
                alt="Engraved statue in gold sunglasses drinking a smoothie — head of A&R"
                className="block w-full object-cover object-top"
                style={{ maxHeight: "44rem" }}
              />
            </div>
          </div>
        </div>
      </section>

      {/* ---- roster marquee on a cobalt hairline shelf ---- */}
      {tracks.length > 0 && (
        <section className="pt-14">
          <div className="rule-double mx-auto max-w-7xl" />
          <div className="mx-auto mb-8 mt-8 flex max-w-7xl flex-wrap items-baseline justify-between gap-x-8 gap-y-2 px-5">
            <h2 className="font-display display-tight text-3xl text-ink sm:text-4xl">
              Now on the roster
            </h2>
            <Link
              href="/roster"
              className="mono-label text-xs text-cobalt transition-colors hover:text-cobalt-hover"
            >
              Full roster →
            </Link>
          </div>
          <div className="overflow-hidden pb-6 pt-2">
            <div className="marquee flex w-max gap-6 pl-5">
              {[...tracks, ...tracks].map((t, i) => (
                <Link
                  key={`${t.slug}-${i}`}
                  href={`/track/${t.slug}`}
                  className={`block w-60 shrink-0 transition-transform hover:-translate-y-1 ${
                    i % 3 === 1 ? "tilt-l" : i % 3 === 2 ? "tilt-r" : ""
                  }`}
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
          {/* the shelf */}
          <div className="rule-line" />
        </section>
      )}

      {/* ---- how the label works: four engraved steps ---- */}
      <section className="grain relative">
        <div className="mx-auto max-w-7xl px-5 py-24">
          <p className="mono-label text-[11px] text-cobalt">How the label works</p>
          <h2 className="font-display display-tight mt-4 max-w-3xl text-4xl text-ink sm:text-6xl">
            From clone to chart in one session
          </h2>
          <div className="mt-14 grid gap-10 sm:grid-cols-2 lg:grid-cols-4">
            {PIPELINE.map((s) => (
              <div key={s.n} className="rule-line pt-5">
                <span className="mono-label text-xs text-cobalt">{s.n}</span>
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
