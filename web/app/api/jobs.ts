// In-memory job store. globalThis so it survives dev HMR and is shared
// between the sign and status route bundles.
// ponytail: memory-only, jobs vanish on server restart — fine for a demo box.

export type Job = {
  stage: "starting" | "intel" | "lyrics" | "audio" | "done" | "error";
  fact?: string;
  title?: string;
  slug?: string;
  startedAt: number;
  stageTimes: Partial<Record<string, number>>; // stage -> epoch ms entered
  error?: string;
  log: string[]; // stdout/stderr tail
};

const g = globalThis as unknown as { __dtJobs?: Map<string, Job> };
export const jobs: Map<string, Job> = (g.__dtJobs ??= new Map());
