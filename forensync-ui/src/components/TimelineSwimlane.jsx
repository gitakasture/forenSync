import { useMemo, useState } from "react";

const COLOR_PALETTE = [
  "bg-teal", "bg-amber", "bg-blue-400", "bg-purple-400",
  "bg-red-400", "bg-pink-400", "bg-green-400", "bg-cyan-400",
];

const NUM_BUCKETS = 60;
const ROW_HEIGHT = 44;
const MIN_WINDOW_MS = 60 * 1000; // don't allow zooming in past 1 minute

function formatAxisTime(ms) {
  const d = new Date(ms);
  return d.toISOString().slice(11, 16) + " " + d.toISOString().slice(0, 10);
}

export default function TimelineSwimlane({ events, onSelectEvent }) {
  const [expandedBucket, setExpandedBucket] = useState(null);

  const timed = useMemo(() => events.filter((e) => e.timestamp), [events]);
  const sources = useMemo(() => [...new Set(timed.map((e) => e.source))].sort(), [timed]);

  const { fullEarliestMs, fullLatestMs } = useMemo(() => {
    if (timed.length === 0) return { fullEarliestMs: 0, fullLatestMs: 1 };
    const times = timed.map((e) => new Date(e.timestamp).getTime());
    return { fullEarliestMs: Math.min(...times), fullLatestMs: Math.max(...times) };
  }, [timed]);

  // The currently VISIBLE window — starts equal to the full range, narrows as you zoom
  const [viewStart, setViewStart] = useState(null);
  const [viewEnd, setViewEnd] = useState(null);

  const effectiveStart = viewStart ?? fullEarliestMs;
  const effectiveEnd = viewEnd ?? fullLatestMs;
  const viewSpan = Math.max(effectiveEnd - effectiveStart, 1);

  const handleZoom = (factor) => {
    const center = (effectiveStart + effectiveEnd) / 2;
    let newSpan = viewSpan * factor;
    const fullSpan = fullLatestMs - fullEarliestMs;
    newSpan = Math.max(MIN_WINDOW_MS, Math.min(newSpan, fullSpan));

    let newStart = center - newSpan / 2;
    let newEnd = center + newSpan / 2;

    if (newStart < fullEarliestMs) {
      newStart = fullEarliestMs;
      newEnd = newStart + newSpan;
    }
    if (newEnd > fullLatestMs) {
      newEnd = fullLatestMs;
      newStart = newEnd - newSpan;
    }
    setViewStart(newStart);
    setViewEnd(newEnd);
  };

  const handlePan = (direction) => {
    const shift = viewSpan * 0.25 * direction;
    let newStart = effectiveStart + shift;
    let newEnd = effectiveEnd + shift;

    if (newStart < fullEarliestMs) {
      newStart = fullEarliestMs;
      newEnd = newStart + viewSpan;
    }
    if (newEnd > fullLatestMs) {
      newEnd = fullLatestMs;
      newStart = newEnd - viewSpan;
    }
    setViewStart(newStart);
    setViewEnd(newEnd);
  };

  const handleFit = () => {
    setViewStart(null);
    setViewEnd(null);
  };

  const lanes = useMemo(() => {
    const laneMap = {};
    sources.forEach((s) => (laneMap[s] = {}));
    timed.forEach((e) => {
      const t = new Date(e.timestamp).getTime();
      if (t < effectiveStart || t > effectiveEnd) return; // outside the visible window
      let bucket = Math.floor(((t - effectiveStart) / viewSpan) * NUM_BUCKETS);
      bucket = Math.min(Math.max(bucket, 0), NUM_BUCKETS - 1);
      if (!laneMap[e.source][bucket]) laneMap[e.source][bucket] = [];
      laneMap[e.source][bucket].push(e);
    });
    return laneMap;
  }, [timed, sources, effectiveStart, effectiveEnd, viewSpan]);

  const axisTicks = useMemo(() => {
    const count = 6;
    return Array.from({ length: count + 1 }, (_, i) => effectiveStart + (viewSpan * i) / count);
  }, [effectiveStart, viewSpan]);

  const isZoomedOrPanned = viewStart !== null;

  if (timed.length === 0) {
    return (
      <p className="rounded-sm border border-hairline bg-panel px-4 py-6 text-center text-sm text-ash">
        No timestamped events to display.
      </p>
    );
  }

  return (
    <div className="rounded-sm border border-hairline bg-panel p-4">
      <div className="mb-3 flex items-center justify-end gap-2">
        <button onClick={() => handlePan(-1)} className="rounded-sm border border-hairline px-2 py-1 text-xs text-ash hover:border-amber hover:text-amber" title="Pan left">◀</button>
        <button onClick={() => handleZoom(1.5)} className="rounded-sm border border-hairline px-2 py-1 text-xs text-ash hover:border-amber hover:text-amber" title="Zoom out">－</button>
        <button onClick={() => handleZoom(0.5)} className="rounded-sm border border-hairline px-2 py-1 text-xs text-ash hover:border-amber hover:text-amber" title="Zoom in">＋</button>
        <button onClick={() => handlePan(1)} className="rounded-sm border border-hairline px-2 py-1 text-xs text-ash hover:border-amber hover:text-amber" title="Pan right">▶</button>
        <button
          onClick={handleFit}
          disabled={!isZoomedOrPanned}
          className="rounded-sm border border-hairline px-3 py-1 text-xs text-ash hover:border-amber hover:text-amber disabled:opacity-40"
        >
          Fit
        </button>
      </div>

      <div className="relative mb-2 h-5 border-b border-hairline pl-36">
        {axisTicks.map((ms, i) => (
          <span
            key={i}
            className="absolute -translate-x-1/2 font-mono text-[10px] text-ash"
            style={{ left: `${(i / (axisTicks.length - 1)) * 100}%` }}
          >
            {formatAxisTime(ms)}
          </span>
        ))}
      </div>

      <div className="space-y-1">
        {sources.map((source, sIdx) => (
          <div key={source} className="flex items-center gap-3">
            <div className="w-32 shrink-0 truncate text-xs text-paper">{source}</div>
            <div className="relative flex-1 rounded-sm bg-ink" style={{ height: ROW_HEIGHT }}>
              {Object.entries(lanes[source] || {}).map(([bucket, bucketEvents]) => {
                const leftPct = ((Number(bucket) + 0.5) / NUM_BUCKETS) * 100;
                const color = COLOR_PALETTE[sIdx % COLOR_PALETTE.length];
                const isCluster = bucketEvents.length > 1;

                return (
                  <button
                    key={bucket}
                    onClick={() => {
                      if (isCluster) {
                        const isSame = expandedBucket?.source === source && expandedBucket?.bucket === bucket;
                        setExpandedBucket(isSame ? null : { source, bucket });
                      } else {
                        onSelectEvent(bucketEvents[0]);
                      }
                    }}
                    title={isCluster ? `${bucketEvents.length} events` : bucketEvents[0].action}
                    className={`absolute top-1/2 flex -translate-x-1/2 -translate-y-1/2 items-center justify-center rounded-full ${color} text-[8px] font-bold leading-none text-ink transition-transform hover:z-10 hover:scale-150`}
                    style={{ left: `${leftPct}%`, width: isCluster ? 20 : 10, height: isCluster ? 20 : 10 }}
                  >
                    {isCluster ? bucketEvents.length : ""}
                  </button>
                );
              })}
            </div>
          </div>
        ))}
      </div>

      {expandedBucket && (
        <div className="mt-4 rounded-sm border border-hairline bg-ink p-3">
          <div className="mb-2 flex items-center justify-between">
            <p className="text-xs uppercase tracking-wide text-ash">
              {expandedBucket.source} — {lanes[expandedBucket.source][expandedBucket.bucket].length} events in this cluster
            </p>
            <button onClick={() => setExpandedBucket(null)} className="text-xs text-ash hover:text-amber">
              Close
            </button>
          </div>
          <div className="max-h-40 space-y-1 overflow-y-auto">
            {lanes[expandedBucket.source][expandedBucket.bucket].map((e) => (
              <button
                key={e.id}
                onClick={() => onSelectEvent(e)}
                className="block w-full rounded-sm px-2 py-1.5 text-left text-xs text-paper hover:bg-panel"
              >
                <span className="font-mono text-ash">{e.timestamp?.slice(11, 19)}</span> — {e.action} ({e.actor})
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}