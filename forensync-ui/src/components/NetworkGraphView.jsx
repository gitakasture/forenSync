import { useMemo, useRef, useState } from "react";
import ForceGraph2D from "react-force-graph-2d";

const ACTOR_COLOR = "#E8A33D";
const HOST_COLOR = "#4FB6B0";

export default function NetworkGraphView({ events, onSelectEvent }) {
  const fgRef = useRef();
  const [selectedNode, setSelectedNode] = useState(null);

  const { nodes, links } = useMemo(() => {
    const nodeMap = new Map();
    const linkMap = new Map();

    const getNode = (id, type) => {
      const key = `${type}:${id}`;
      if (!nodeMap.has(key)) {
        nodeMap.set(key, { id: key, label: id, type, degree: 0, eventCount: 0 });
      }
      return nodeMap.get(key);
    };

    for (const e of events) {
      if (!e.actor || !e.host) continue;
      const actorNode = getNode(e.actor, "actor");
      const hostNode = getNode(e.host, "host");

      const linkKey = `${actorNode.id}::${hostNode.id}`;
      if (!linkMap.has(linkKey)) {
        linkMap.set(linkKey, { source: actorNode.id, target: hostNode.id, count: 0, events: [] });
        actorNode.degree += 1;
        hostNode.degree += 1;
      }
      const link = linkMap.get(linkKey);
      link.count += 1;
      link.events.push(e);
      actorNode.eventCount += 1;
      hostNode.eventCount += 1;
    }

    // const limitedNodes = [...nodeMap.values()].slice(0, 100);
    // const nodeIds = new Set(limitedNodes.map(n => n.id));

    // const limitedLinks = [...linkMap.values()].filter(
    //   l => nodeIds.has(l.source) && nodeIds.has(l.target)
    // );

    return { nodes: [...nodeMap.values()], links: [...linkMap.values()] };
  }, [events]);

  const nodeEvents = useMemo(() => {
    if (!selectedNode) return [];
    return events.filter((e) =>
      selectedNode.type === "actor" ? e.actor === selectedNode.label : e.host === selectedNode.label
    );
  }, [selectedNode, events]);

  if (nodes.length === 0) {
    return (
      <p className="rounded-sm border border-hairline bg-panel px-4 py-6 text-center text-sm text-ash">
        No actor/host data to visualize.
      </p>
    );
  }

  return (
    <div className="rounded-sm border border-hairline bg-panel p-2">
      <div className="mb-2 flex items-center gap-4 px-2 pt-2">
        <span className="flex items-center gap-1.5 text-xs text-ash">
          <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: ACTOR_COLOR }} /> Actor
        </span>
        <span className="flex items-center gap-1.5 text-xs text-ash">
          <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: HOST_COLOR }} /> Host
        </span>
        <span className="text-xs text-ash">
          {nodes.length} nodes · {links.length} connections
        </span>
      </div>

      <div style={{ height: 480 }}>
        {console.log(nodes.length, links.length)}
        <ForceGraph2D
          ref={fgRef}
          graphData={{ nodes, links }}
          backgroundColor="#12161B"
          nodeLabel={(n) => `${n.type}: ${n.label} (${n.eventCount} events)`}
          nodeColor={(n) => (n.type === "actor" ? ACTOR_COLOR : HOST_COLOR)}
          nodeVal={(n) => Math.max(2, Math.sqrt(n.degree) * 3)}
          linkColor={() => "rgba(139, 147, 160, 0.35)"}
          linkWidth={(l) => Math.min(1 + Math.log2(l.count), 8)}
          linkLabel={(l) => `${l.count} event(s)`}
          onNodeClick={(n) => setSelectedNode(n)}
          cooldownTicks={80}
        />
      </div>

      {/* <div style={{ height: 480 }}>
        <h1 style={{ color: "white" }}>
          Graph Component Loaded
        </h1>
      </div> */}

      {selectedNode && (
        <div className="mt-2 rounded-sm border border-hairline bg-ink p-3">
          <div className="mb-2 flex items-center justify-between">
            <p className="text-xs uppercase tracking-wide text-ash">
              {selectedNode.type}: <span className="text-paper">{selectedNode.label}</span> — {nodeEvents.length} event(s)
            </p>
            <button onClick={() => setSelectedNode(null)} className="text-xs text-ash hover:text-amber">
              Close
            </button>
          </div>
          <div className="max-h-40 space-y-1 overflow-y-auto">
            {nodeEvents.slice(0, 100).map((e) => (
              <button
                key={e.id}
                onClick={() => onSelectEvent(e)}
                className="block w-full rounded-sm px-2 py-1.5 text-left text-xs text-paper hover:bg-panel"
              >
                <span className="font-mono text-ash">{e.timestamp?.slice(11, 19) || "—"}</span> — {e.action} ({e.actor} → {e.host})
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}