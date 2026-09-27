import { useMemo, useState } from "react";

const NUM_BUCKETS = 40;
const BAR_COLOR = "bg-amber";

function formatAxisTime(ms) {
  const d = new Date(ms);
  const datePart = d.toISOString().slice(5, 10).replace("-", "/"); // MM/DD
  const timePart = d.toISOString().slice(11, 16); // HH:MM
  return `${datePart} ${timePart}`;
}

export default function ActivityHistogram({ events, onSelectEvent }) {
  const [expandedBucket, setExpandedBucket] = useState(null);

  const timed = useMemo(() => events.filter((e) => e.timestamp), [events]);

  const { earliestMs, latestMs } = useMemo(() => {
    if (timed.length === 0) return { earliestMs: 0, latestMs: 1 };
    const times = timed.map((e) => new Date(e.timestamp).getTime());
    return { earliestMs: Math.min(...times), latestMs: Math.max(...times) };
  }, [timed]);

  const span = Math.max(latestMs - earliestMs, 1);

  const buckets = useMemo(() => {
    const arr = Array.from({ length: NUM_BUCKETS }, () => []);
    timed.forEach((e) => {
      const t = new Date(e.timestamp).getTime();
      let idx = Math.floor(((t - earliestMs) / span) * NUM_BUCKETS);
      idx = Math.min(Math.max(idx, 0), NUM_BUCKETS - 1);
      arr[idx].push(e);
    });
    return arr;
  }, [timed, earliestMs, span]);

  const maxCount = Math.max(...buckets.map((b) => b.length), 1);

  const axisTicks = useMemo(() => {
    const count = 5;
    return Array.from({ length: count + 1 }, (_, i) => earliestMs + (span * i) / count);
  }, [earliestMs, span]);

  if (timed.length === 0) {
    return (
      <p className="rounded-sm border border-hairline bg-panel px-4 py-6 text-center text-sm text-ash">
        No timestamped events to display.
      </p>
    );
  }

  return (
    <div className="rounded-sm border border-hairline bg-panel p-4">
      <div className="mb-3 flex items-center justify-between px-1">
        <p className="text-xs uppercase tracking-wide text-ash">Events</p>
        <p className="text-xs text-ash">Peak: {maxCount} events in one interval</p>
      </div>

      <div className="flex h-48 items-end gap-1 border-b border-l border-hairline px-2 pb-1">
        {buckets.map((bucketEvents, i) => {
          const heightPct = (bucketEvents.length / maxCount) * 100;
          const isSpike = bucketEvents.length > maxCount * 0.6 && bucketEvents.length > 3;
          return (
            <button
              key={i}
              onClick={() => bucketEvents.length > 0 && setExpandedBucket(expandedBucket === i ? null : i)}
              disabled={bucketEvents.length === 0}
              title={`${bucketEvents.length} event(s)`}
              className={`group relative flex-1 rounded-t-sm transition-all ${
                bucketEvents.length === 0 ? "bg-transparent" : isSpike ? "bg-danger hover:opacity-80" : `${BAR_COLOR} hover:opacity-80`
              }`}
              style={{ height: `${Math.max(heightPct, bucketEvents.length > 0 ? 2 : 0)}%` }}
            />
          );
        })}
      </div>

      <div className="relative mt-1.5 h-4 overflow-hidden px-2">
        {axisTicks.map((ms, i) => {
          const isFirst = i === 0;
          const isLast = i === axisTicks.length - 1;
          return (
            <span
              key={i}
              className={`absolute whitespace-nowrap font-mono text-[10px] text-ash ${
                isFirst ? "left-2" : isLast ? "right-2" : "-translate-x-1/2"
              }`}
              style={!isFirst && !isLast ? { left: `${(i / (axisTicks.length - 1)) * 100}%` } : undefined}
            >
              {formatAxisTime(ms)}
            </span>
          );
        })}
      </div>

      <div className="mt-3 flex items-center gap-4 px-1 text-[11px] text-ash">
        <span className="flex items-center gap-1.5">
          <span className="h-2.5 w-2.5 rounded-sm bg-amber" /> Normal activity
        </span>
        <span className="flex items-center gap-1.5">
          <span className="h-2.5 w-2.5 rounded-sm bg-danger" /> Spike (possible burst)
        </span>
      </div>

      {expandedBucket !== null && (
        <div className="mt-4 rounded-sm border border-hairline bg-ink p-3">
          <div className="mb-2 flex items-center justify-between">
            <p className="text-xs uppercase tracking-wide text-ash">
              {buckets[expandedBucket].length} event(s) in this interval
            </p>
            <button onClick={() => setExpandedBucket(null)} className="text-xs text-ash hover:text-amber">
              Close
            </button>
          </div>
          <div className="max-h-40 space-y-1 overflow-y-auto">
            {buckets[expandedBucket].slice(0, 100).map((e) => (
              <button
                key={e.id}
                onClick={() => onSelectEvent(e)}
                className="block w-full rounded-sm px-2 py-1.5 text-left text-xs text-paper hover:bg-panel"
              >
                <span className="font-mono text-ash">{e.timestamp?.slice(11, 19)}</span> — {e.action} ({e.actor} → {e.host})
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}