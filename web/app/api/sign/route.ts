import { spawn } from "child_process";
import { NextResponse } from "next/server";
import { PRESETS } from "@/lib/presets";
import { jobs, type Job } from "../jobs";

const PYTHON = "/Users/vrajpatel/Developer/droptable/.venv/bin/python";
const CWD = "/Users/vrajpatel/Developer/droptable";

export async function POST(req: Request) {
  const body = await req.json().catch(() => ({}));
  const repo = String(body.repo ?? "")
    .trim()
    .replace(/^https?:\/\/(www\.)?github\.com\//, "")
    .replace(/\.git$/, "")
    .replace(/\/+$/, "");
  const style = String(body.style ?? "");

  if (!/^[\w.-]+\/[\w.-]+$/.test(repo)) {
    return NextResponse.json(
      { error: "Paste a GitHub repo URL or owner/name." },
      { status: 400 },
    );
  }
  if (!(style in PRESETS)) {
    return NextResponse.json({ error: "Unknown style." }, { status: 400 });
  }

  const id = crypto.randomUUID();
  const job: Job = { stage: "starting", startedAt: Date.now(), stageTimes: {}, log: [] };
  jobs.set(id, job);

  const child = spawn(
    PYTHON,
    ["pipeline/run.py", "--repo", repo, "--style", style, "--takes", "1", "--pick", "1", "--duration", "75"],
    { cwd: CWD },
  );

  const logLine = (l: string) => {
    job.log.push(l);
    if (job.log.length > 40) job.log.shift();
  };

  const handle = (line: string) => {
    const l = line.trim();
    if (!l) return;
    logLine(l);
    const done = l.match(/^STAGE:done SLUG:(.+)$/);
    if (done) {
      job.slug = done[1].trim();
      job.stageTimes.done = Date.now();
      job.stage = "done";
      return;
    }
    const stage = l.match(/^STAGE:(intel|lyrics|audio)\b/);
    if (stage) {
      job.stage = stage[1] as Job["stage"];
      job.stageTimes[stage[1]] = Date.now();
      return;
    }
    if (l.startsWith("FACT:")) job.fact = l.slice(5).trim();
    if (l.startsWith("TITLE:")) job.title = l.slice(6).trim();
  };

  let buf = "";
  child.stdout.on("data", (d: Buffer) => {
    buf += d.toString();
    const lines = buf.split("\n");
    buf = lines.pop() ?? "";
    lines.forEach(handle);
  });
  child.stderr.on("data", (d: Buffer) => {
    d.toString().split("\n").forEach((l) => l.trim() && logLine(l.trim()));
  });
  child.on("close", (code) => {
    if (buf.trim()) handle(buf);
    if (job.stage !== "done") {
      job.stage = "error";
      job.error = `pipeline exited with code ${code}`;
    }
  });
  child.on("error", (e) => {
    job.stage = "error";
    job.error = String(e);
  });

  return NextResponse.json({ job: id });
}
