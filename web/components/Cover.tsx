import { artForRepo } from "@/lib/art";
import { presetFor } from "@/lib/presets";

// Album cover: deterministic classical art per repo, duotoned with the style's
// accent. Server-safe, pure CSS. Text scales with container width (cqw), so it
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
  const art = artForRepo(repo);

  return (
    <div
      className="grain relative aspect-square w-full overflow-hidden bg-bg-raised select-none"
      style={{ containerType: "inline-size" }}
    >
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        src={art}
        alt=""
        className="absolute inset-0 h-full w-full object-cover"
        style={{ filter: "grayscale(1) contrast(1.15) brightness(0.92)" }}
      />
      {/* accent duotone: multiply pushes highlights toward the accent */}
      <div
        className="absolute inset-0"
        style={{
          background: `linear-gradient(160deg, ${accent} 0%, ${accent}cc 55%, #1a1510 130%)`,
          mixBlendMode: "multiply",
        }}
      />
      {/* legibility scrim behind the type */}
      <div
        className="absolute inset-0"
        style={{
          background: "linear-gradient(to top, rgba(10,8,6,0.82) 0%, rgba(10,8,6,0.25) 38%, transparent 62%)",
        }}
      />

      <div
        className="absolute inset-0 z-10 flex flex-col justify-between"
        style={{ padding: size === "lg" ? "5cqw" : "6cqw" }}
      >
        <div className="flex items-start justify-between" style={{ fontSize: "3cqw" }}>
          <span className="uppercase" style={{ letterSpacing: "0.25em", color: "rgba(236,227,210,0.85)" }}>
            Signed to DropTable Records
          </span>
          <span className="font-display" style={{ color: accent, filter: "brightness(1.6)" }}>
            33⅓
          </span>
        </div>

        <div>
          <h3
            className="font-display display-tight break-words text-paper"
            style={{ fontSize: "12cqw", paddingRight: "18cqw", textShadow: "0 2px 24px rgba(0,0,0,0.5)" }}
          >
            {title}
          </h3>
          <p
            className="uppercase"
            style={{ fontSize: "3.2cqw", letterSpacing: "0.3em", marginTop: "2cqw", color: "rgba(236,227,210,0.75)" }}
          >
            {artist}
          </p>
        </div>
      </div>

      {/* parental-advisory-style sticker */}
      <div
        className="absolute z-20 bg-paper text-center font-bold uppercase text-black"
        style={{
          right: "5cqw",
          bottom: "5cqw",
          padding: "1.6cqw 2.2cqw",
          fontSize: "2.6cqw",
          lineHeight: 1.25,
          letterSpacing: "0.12em",
          border: "0.5cqw solid #0d0b09",
          boxShadow: "0 0 0 0.5cqw rgba(227,217,194,0.9)",
        }}
      >
        Explicit
        <br />
        Code
      </div>
    </div>
  );
}
