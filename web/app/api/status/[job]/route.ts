import { NextResponse } from "next/server";
import { jobs } from "../../jobs";

export async function GET(
  _req: Request,
  { params }: { params: Promise<{ job: string }> },
) {
  const { job } = await params;
  const j = jobs.get(job);
  if (!j) return NextResponse.json({ error: "unknown job" }, { status: 404 });
  // now: server clock, so the client can render elapsed without skew.
  return NextResponse.json({ ...j, now: Date.now() });
}
