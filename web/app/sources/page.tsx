import { getSourceReviewQueue } from "@/lib/data";

export const metadata = { title: "Source Review Queue — DropTable Records" };

export default function SourcesPage() {
  const records = getSourceReviewQueue();
  const pending = records.filter((record) => record.reviewerDecision === "pending").length;

  return (
    <div className="mx-auto max-w-7xl px-5 py-12 sm:py-16">
      <p className="mono-label text-[11px] text-cobalt">Research intake</p>
      <h1 className="font-display display-tight mt-3 text-6xl text-ink sm:text-8xl">
        Source review queue
      </h1>
      <div className="rule-double mt-6" />
      <div className="mt-5 flex flex-wrap gap-x-8 gap-y-2 text-sm text-ink-dim">
        <p>{records.length} source records</p>
        <p>{pending} awaiting human review</p>
        <p>Metadata only — no lyrics, transcripts, or media are stored.</p>
      </div>

      <div className="mt-10 overflow-x-auto border border-line bg-card">
        <table className="min-w-[980px] w-full border-collapse text-left text-xs">
          <thead className="border-b border-line bg-paper text-[10px] uppercase tracking-[0.16em] text-ink-dim">
            <tr>
              <th className="px-4 py-3">Source</th>
              <th className="px-4 py-3">Collection</th>
              <th className="px-4 py-3">Type</th>
              <th className="px-4 py-3">Rights / trust</th>
              <th className="px-4 py-3">Extraction</th>
              <th className="px-4 py-3">Linked records</th>
              <th className="px-4 py-3">Review</th>
            </tr>
          </thead>
          <tbody>
            {records.map((record) => (
              <tr key={record.id} className="border-b border-line last:border-0">
                <td className="max-w-72 px-4 py-4 align-top">
                  <p className="font-medium text-ink">{record.sourceName}</p>
                  <a
                    href={record.sourceUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="mt-1 block truncate font-mono text-[10px] text-cobalt underline-offset-2 hover:underline"
                  >
                    {record.sourceUrl}
                  </a>
                </td>
                <td className="px-4 py-4 align-top">
                  <div className="flex max-w-52 flex-wrap gap-1">
                    {record.collectionTags.map((tag) => (
                      <span key={tag} className="border border-line px-1.5 py-0.5 text-[9px] text-ink-dim">
                        {tag}
                      </span>
                    ))}
                  </div>
                </td>
                <td className="px-4 py-4 align-top font-mono text-[10px] text-ink-dim">{record.sourceType}</td>
                <td className="px-4 py-4 align-top">
                  <p>{record.rightsStatus}</p>
                  <p className="mt-1 text-ink-dim">{record.trustLevel}</p>
                </td>
                <td className="px-4 py-4 align-top">{record.extractionStatus}</td>
                <td className="px-4 py-4 align-top">{record.linkedCatalogRecordCount}</td>
                <td className="px-4 py-4 align-top">
                  <span className="mono-label border border-gold px-2 py-1 text-[9px] text-gold">
                    {record.reviewerDecision}
                  </span>
                  {record.rejectionReason && <p className="mt-1 text-ink-dim">{record.rejectionReason}</p>}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
