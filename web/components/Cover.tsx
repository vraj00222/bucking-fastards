import { artForRepo } from "@/lib/art";
import { presetFor } from "@/lib/presets";

// Album cover as an engraved catalog plate: paper card, cobalt-duotone
// classical art per repo, thin double border, gold EXPLICIT CODE sticker.
// Server-safe, pure CSS. Text scales with container width (cqw), so it
// holds up from 300px to 800px; size only tunes padding.
export default function Cover({
  repo,
  style,
  title,
  artist,
  size = "sm",
}: {
  repo: string;
  style: string;
  title: string;
  artist: string;
  size?: "sm" | "lg";
}) {
  const { accent } = presetFor(style);
  const art = artForRepo(repo + style);

  return (
    <div
      className="relative flex aspect-square w-full select-none flex-col overflow-hidden bg-card text-ink"
      style={{
        containerType: "inline-size",
        border: "3px double var(--cobalt)",
        // % (not cqw): the card is itself the container, so its own cqw units
        // would resolve against the viewport and blow up the padding.
        padding: size === "lg" ? "3.5%" : "4%",
        boxShadow: "0 2px 8px rgba(30,58,158,0.12)",
      }}
    >
      {/* catalog-card header line */}
      <div className="flex items-baseline justify-between" style={{ fontSize: "2.6cqw" }}>
        <span className="mono-label text-ink-dim">Signed to DropTable Records</span>
        <span className="font-display" style={{ color: "var(--gold)" }}>
          33⅓
        </span>
      </div>

      {/* engraved art plate: cobalt duotone on paper */}
      <div
        className="duotone-cobalt relative mt-[2.5cqw] flex-1 overflow-hidden"
        style={{ border: "1px solid var(--cobalt)" }}
      >
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img src={art} alt="" className="absolute inset-0 h-full w-full object-cover" />

        {/* gold-outlined parental-advisory sticker, pasted in */}
        <div
          className="absolute z-10 bg-card text-center font-bold uppercase"
          style={{
            right: "3.5cqw",
            bottom: "3.5cqw",
            rotate: "-2deg",
            padding: "1.4cqw 2cqw",
            fontSize: "2.4cqw",
            lineHeight: 1.25,
            letterSpacing: "0.12em",
            color: "var(--ink)",
            border: "0.5cqw solid var(--gold)",
            boxShadow: "0 2px 8px rgba(30,58,158,0.12)",
          }}
        >
          Explicit
          <br />
          Code
        </div>
      </div>

      {/* plate label: style-accent title, small-caps mono artist */}
      <div style={{ paddingTop: "3cqw" }}>
        <h3
          className="font-display display-tight break-words"
          style={{ fontSize: "9.5cqw", color: accent }}
        >
          {title}
        </h3>
        <p
          className="mono-label"
          style={{ fontSize: "2.8cqw", marginTop: "1.6cqw", color: "var(--ink-dim)" }}
        >
          {artist}
        </p>
      </div>
    </div>
  );
}
