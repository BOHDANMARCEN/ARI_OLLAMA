import { useEffect, useRef, useState, useCallback } from "react";
import ForceGraph2D from "react-force-graph-2d";

type GraphNode = {
  id: string;
  group: string;
  value: number;
  label?: string;
  text?: string;
  x?: number;
  y?: number;
};

type GraphLink = {
  source: string;
  target: string;
};

type GraphData = {
  nodes: GraphNode[];
  links: GraphLink[];
};

const groupColors: Record<string, string> = {
  voice: "#f97316",
  core: "#3b82f6",
  thought: "#a855f7",
  goal: "#22c55e",
  belief: "#eab308",
  metric: "#ec4899",
};

const MIN_WIDTH = 260;
const MIN_HEIGHT = 180;
const DEFAULT_WIDTH = 280;
const DEFAULT_HEIGHT = 200;
const EXPANDED_WIDTH = 600;
const EXPANDED_HEIGHT = 400;

export default function BrainGraph() {
  const [graphData, setGraphData] = useState<GraphData>({ nodes: [], links: [] });
  const [isExpanded, setIsExpanded] = useState(false);
  const [dimensions, setDimensions] = useState({ width: DEFAULT_WIDTH, height: DEFAULT_HEIGHT });
  const [isResizing, setIsResizing] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const graphRef = useRef<any>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const resizeStartRef = useRef({ x: 0, y: 0, width: 0, height: 0 });

  useEffect(() => {
    const ws = new WebSocket("ws://localhost:3000/ws");
    wsRef.current = ws;

    ws.onopen = () => {
      console.log("[BrainGraph] WebSocket connected");
    };

    ws.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);
        if (payload.type === "brain_graph" && payload.graph) {
          setGraphData(payload.graph);
        }
        if (payload.type === "dashboard_snapshot" && payload.brain_graph) {
          setGraphData(payload.brain_graph);
        }
      } catch (e) {
        console.error("[BrainGraph] Parse error:", e);
      }
    };

    ws.onclose = () => {
      console.log("[BrainGraph] WebSocket disconnected");
    };

    ws.onerror = (error) => {
      console.error("[BrainGraph] WebSocket error:", error);
    };

    return () => {
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.close();
      }
    };
  }, []);

  const handleNodeClick = useCallback((node: GraphNode) => {
    console.log("[BrainGraph] Node clicked:", node);
  }, []);

  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    if ((e.target as HTMLElement).classList.contains("resize-handle")) {
      setIsResizing(true);
      resizeStartRef.current = {
        x: e.clientX,
        y: e.clientY,
        width: dimensions.width,
        height: dimensions.height,
      };
      e.preventDefault();
    }
    if ((e.target as HTMLElement).classList.contains("expand-handle")) {
      setIsDragging(true);
      e.preventDefault();
    }
  }, [dimensions]);

  const handleMouseMove = useCallback((e: React.MouseEvent | MouseEvent) => {
    if (isResizing) {
      const deltaX = e.clientX - resizeStartRef.current.x;
      const deltaY = e.clientY - resizeStartRef.current.y;
      const newWidth = Math.max(MIN_WIDTH, resizeStartRef.current.width + deltaX);
      const newHeight = Math.max(MIN_HEIGHT, resizeStartRef.current.height + deltaY);
      setDimensions({ width: newWidth, height: newHeight });
    }
  }, [isResizing]);

  const handleMouseUp = useCallback(() => {
    setIsResizing(false);
    setIsDragging(false);
  }, []);

  useEffect(() => {
    if (isResizing || isDragging) {
      window.addEventListener("mousemove", handleMouseMove as any);
      window.addEventListener("mouseup", handleMouseUp);
      return () => {
        window.removeEventListener("mousemove", handleMouseMove as any);
        window.removeEventListener("mouseup", handleMouseUp);
      };
    }
  }, [isResizing, isDragging, handleMouseMove, handleMouseUp]);

  const handleDoubleClick = useCallback(() => {
    setIsExpanded((prev) => !prev);
    setDimensions((prev) => ({
      width: prev.width === DEFAULT_WIDTH ? EXPANDED_WIDTH : DEFAULT_WIDTH,
      height: prev.height === DEFAULT_HEIGHT ? EXPANDED_HEIGHT : DEFAULT_HEIGHT,
    }));
  }, []);

  const nodeCanvasObject = useCallback(
    (node: GraphNode, ctx: CanvasRenderingContext2D, globalScale: number) => {
      const label = node.label || node.id;
      const fontSize = 12 / globalScale;
      const nodeRadius = Math.sqrt(node.value) * 2;

      ctx.beginPath();
      ctx.arc(node.x || 0, node.y || 0, nodeRadius, 0, 2 * Math.PI);
      ctx.fillStyle = groupColors[node.group] || "#6b7280";
      ctx.fill();

      ctx.font = `${fontSize}px Sans-Serif`;
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillStyle = "#ffffff";
      ctx.fillText(label, node.x || 0, node.y || 0 + nodeRadius + fontSize + 2);

      if (node.text) {
        const subFontSize = Math.max(6, fontSize - 2);
        ctx.font = `${subFontSize}px Sans-Serif`;
        ctx.fillStyle = "#9ca3af";
        ctx.fillText(node.text.substring(0, 30), node.x || 0, node.y || 0 + nodeRadius + fontSize + subFontSize + 6);
      }
    },
    []
  );

  return (
    <section className="panel brain-graph-panel">
      <div className="panel-header">
        <span>Brain Graph</span>
        <button
          className="text-button"
          onClick={() => {
            setIsExpanded(!isExpanded);
            setDimensions({
              width: isExpanded ? DEFAULT_WIDTH : EXPANDED_WIDTH,
              height: isExpanded ? DEFAULT_HEIGHT : EXPANDED_HEIGHT,
            });
          }}
          type="button"
        >
          {isExpanded ? "Collapse" : "Expand"}
        </button>
      </div>

      <div
        ref={containerRef}
        className={`brain-graph-container ${isExpanded ? "expanded" : ""}`}
        onMouseDown={handleMouseDown}
        onDoubleClick={handleDoubleClick}
        style={{ width: dimensions.width, height: dimensions.height }}
      >
        <div className="resize-handle resize-se" />

        {graphData.nodes.length === 0 ? (
          <div className="graph-empty">
            <p>Waiting for brain data...</p>
          </div>
        ) : (
          <ForceGraph2D
            ref={graphRef}
            graphData={graphData}
            nodeLabel={(node: any) => node.label || node.id}
            nodeCanvasObject={nodeCanvasObject}
            nodeVal={(node: any) => Math.sqrt(node.value) * 3}
            nodeAutoColorBy="group"
            linkColor={() => "#374151"}
            linkWidth={1}
            linkDirectionalParticles={2}
            linkDirectionalParticleSpeed={0.005}
            linkDirectionalParticleWidth={2}
            linkDirectionalParticleColor={() => "#60a5fa"}
            backgroundColor="#0f172a"
            width={dimensions.width}
            height={dimensions.height}
            cooldownTicks={100}
            onNodeClick={handleNodeClick}
            d3VelocityDecay={0.3}
            d3AlphaDecay={0.02}
          />
        )}
      </div>

      <div className="graph-legend">
        {Object.entries(groupColors).map(([group, color]) => (
          <div key={group} className="legend-item">
            <span className="legend-dot" style={{ backgroundColor: color }} />
            <span>{group}</span>
          </div>
        ))}
        <span className="legend-hint">Double-click or drag corner to resize</span>
      </div>
    </section>
  );
}