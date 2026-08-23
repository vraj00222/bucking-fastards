// Liner notes: [verse]/[chorus] tags become cobalt catalog labels; any line
// containing a mined fact gets a gold underline + paper-yellow wash. Server-safe.
// accent stays in the contract; section furniture keeps to house cobalt/gold.

function escapeRe(s: string) {
  return s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

export default function Lyrics({
  lyrics,
  facts,
}: {
  lyrics: string;
  facts: string[];
  accent?: string;
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
              className="mono-label mt-8 mb-2 flex items-baseline gap-3 text-[11px] text-cobalt first:mt-0"
            >
              {tag[1]}
              <span
                className="h-px w-10 self-center"
                style={{ background: "var(--cobalt)", opacity: 0.4 }}
              />
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
                  className="cursor-help bg-transparent text-ink"
                  style={{
                    borderBottom: "1px solid var(--gold)",
                    boxShadow: "inset 0 -0.45em rgba(195,148,29,0.16)",
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
