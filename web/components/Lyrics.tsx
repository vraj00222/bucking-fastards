// Liner notes: [verse]/[chorus] tags become section labels; any line containing
// a mined fact gets an accent highlight. Server-safe.

function escapeRe(s: string) {
  return s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

export default function Lyrics({
  lyrics,
  facts,
  accent,
}: {
  lyrics: string;
  facts: string[];
  accent: string;
}) {
  // Longest facts first so "npm install commander" wins over "commander".
  const factRe = facts.length
    ? new RegExp(
        `(${[...facts].sort((a, b) => b.length - a.length).map(escapeRe).join("|")})`,
        "gi",
      )
    : null;

  return (
    <div className="max-w-2xl text-[15px] leading-7 text-ink/90">
      {lyrics.split("\n").map((line, i) => {
        const tag = line.match(/^\s*\[(.+)\]\s*$/);
        if (tag) {
          return (
            <p
              key={i}
              className="mt-8 mb-2 flex items-baseline gap-3 text-[11px] font-semibold uppercase tracking-[0.3em] first:mt-0"
              style={{ color: accent }}
            >
              {tag[1]}
              <span className="h-px w-10 self-center" style={{ background: accent, opacity: 0.4 }} />
            </p>
          );
        }
        if (!line.trim()) return null; // spacing comes from section labels
        const parts = factRe ? line.split(factRe) : [line];
        return (
          <p key={i}>
            {parts.map((part, j) =>
              factRe && j % 2 === 1 ? (
                <mark
                  key={j}
                  title="mined from the repo"
                  className="cursor-help bg-transparent"
                  style={{
                    color: "var(--paper)",
                    borderBottom: `1px solid ${accent}`,
                    boxShadow: `inset 0 -0.4em ${accent}26`,
                    textShadow: `0 0 14px ${accent}59`,
                  }}
                >
                  {part}
                </mark>
              ) : (
                part
              ),
            )}
          </p>
        );
      })}
    </div>
  );
}
