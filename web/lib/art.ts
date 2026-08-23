// Actual files in web/public/art ("aesthetic 3.jpg" skipped: space in name).
export const ART_FILES = [
  "aesthetic.jpg",
  "aesthetic2.jpg",
  "bg1.jpg",
  "bg2.jpg",
  "bg3.jpg",
  "bg4.jpg",
  "bg5.jpg",
  "bg6.jpg",
  "bg7.jpg",
  "bg8.jpg",
  "collage.jpeg",
  "herowide.png",
  "herowide2.png",
  "lib1.jpg",
  "lib2.jpg",
  "lib3.jpg",
  "lib4.jpg",
  "lib5.jpg",
  "lib6.jpg",
  "long.jpg",
  "long2.jpg",
  "long3.png",
  "long4.png",
  "long6.jpg",
  "platoreading.jpg",
  "readingimage.jpeg",
  "readingroom.jpg",
  "readingroom2.jpg",
] as const;

// Deterministic: same repo always gets the same cover art.
export function artForRepo(repo: string): string {
  let h = 5381;
  for (let i = 0; i < repo.length; i++) h = ((h * 33) ^ repo.charCodeAt(i)) >>> 0;
  return `/art/${ART_FILES[h % ART_FILES.length]}`;
}
