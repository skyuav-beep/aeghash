import React, { useMemo } from "react";

export type OrganizationStatus = "active" | "hold" | "warning";

export interface OrganizationNode {
  id: string;
  name: string;
  rank: string;
  pvLeft: number;
  pvRight: number;
  status: OrganizationStatus;
  children?: OrganizationNode[];
}

export interface OrganizationTreeCanvasProps {
  root: OrganizationNode;
  zoom?: number;
  onSelectNode?: (node: OrganizationNode) => void;
}

const statusColors: Record<OrganizationStatus, string> = {
  active: "var(--aeg-status-success-background)",
  hold: "var(--aeg-status-warning-background)",
  warning: "var(--aeg-status-danger-background)"
};

const statusTextColors: Record<OrganizationStatus, string> = {
  active: "var(--aeg-status-success-foreground)",
  hold: "var(--aeg-status-warning-foreground)",
  warning: "var(--aeg-status-danger-foreground)"
};

interface LevelNode extends OrganizationNode {
  depth: number;
}

const flattenLevels = (root: OrganizationNode): LevelNode[][] => {
  const queue: LevelNode[] = [{ ...root, depth: 0 }];
  const levels: LevelNode[][] = [];

  while (queue.length > 0) {
    const node = queue.shift()!;
    if (!levels[node.depth]) {
      levels[node.depth] = [];
    }
    levels[node.depth].push(node);
    node.children?.forEach((child) => {
      queue.push({ ...child, depth: node.depth + 1 });
    });
  }

  return levels;
};

export const OrganizationTreeCanvas: React.FC<OrganizationTreeCanvasProps> = ({
  root,
  zoom = 1,
  onSelectNode
}) => {
  const levels = useMemo(() => flattenLevels(root), [root]);

  return (
    <div
      style={{
        position: "relative",
        overflow: "auto",
        background: "var(--aeg-surface-canvas, #fafafa)",
        padding: "32px",
        borderRadius: "16px",
        border: "1px solid var(--aeg-border-subtle, #e0e0e0)"
      }}
      aria-label="조직도 캔버스"
    >
      <div
        style={{
          transform: `scale(${zoom})`,
          transformOrigin: "top center",
          transition: "transform 160ms ease"
        }}
      >
        {levels.map((levelNodes, levelIndex) => (
          <div
            key={`level-${levelIndex}`}
            style={{
              display: "grid",
              gridTemplateColumns: `repeat(${levelNodes.length}, minmax(180px, 1fr))`,
              gap: "24px",
              justifyItems: "center",
              marginBottom: "48px"
            }}
          >
            {levelNodes.map((node) => (
              <button
                key={node.id}
                type="button"
                onClick={() => onSelectNode?.(node)}
                style={{
                  width: "100%",
                  minHeight: "120px",
                  padding: "16px",
                  borderRadius: "16px",
                  border: "1px solid var(--aeg-border-subtle, #dddddd)",
                  background: "var(--aeg-surface-elevated, #ffffff)",
                  boxShadow: "0 12px 24px rgba(15, 15, 15, 0.08)",
                  transition: "transform 120ms ease, box-shadow 120ms ease",
                  textAlign: "left",
                  cursor: "pointer"
                }}
                onMouseDown={(event) => {
                  event.currentTarget.style.transform = "scale(0.98)";
                }}
                onMouseUp={(event) => {
                  event.currentTarget.style.transform = "scale(1)";
                }}
                onMouseLeave={(event) => {
                  event.currentTarget.style.transform = "scale(1)";
                }}
                aria-label={`${node.name}, 직급 ${node.rank}, 좌측 PV ${node.pvLeft}, 우측 PV ${node.pvRight}`}
              >
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                    marginBottom: "8px"
                  }}
                >
                  <span
                    style={{
                      fontSize: "var(--aeg-typography-body-lg-font-size, 16px)",
                      fontWeight: 600,
                      color: "var(--aeg-text-primary, #191919)"
                    }}
                  >
                    {node.name}
                  </span>
                  <span
                    style={{
                      fontSize: "12px",
                      fontWeight: 600,
                      padding: "4px 10px",
                      borderRadius: "999px",
                      background: statusColors[node.status],
                      color: statusTextColors[node.status]
                    }}
                  >
                    {node.status === "active" ? "활성" : node.status === "hold" ? "보류" : "경고"}
                  </span>
                </div>
                <p
                  style={{
                    fontSize: "12px",
                    color: "var(--aeg-text-muted, #6b6b6b)",
                    marginBottom: "12px"
                  }}
                >
                  직급 {node.rank}
                </p>
                <div
                  style={{
                    display: "grid",
                    gridTemplateColumns: "repeat(2, 1fr)",
                    gap: "12px"
                  }}
                  aria-hidden="true"
                >
                  <div>
                    <span
                      style={{
                        display: "block",
                        fontSize: "11px",
                        color: "var(--aeg-text-muted, #6b6b6b)"
                      }}
                    >
                      좌측 PV
                    </span>
                    <strong
                      style={{
                        fontSize: "16px",
                        color: "var(--aeg-text-primary, #191919)"
                      }}
                    >
                      {node.pvLeft.toLocaleString()}
                    </strong>
                  </div>
                  <div>
                    <span
                      style={{
                        display: "block",
                        fontSize: "11px",
                        color: "var(--aeg-text-muted, #6b6b6b)"
                      }}
                    >
                      우측 PV
                    </span>
                    <strong
                      style={{
                        fontSize: "16px",
                        color: "var(--aeg-text-primary, #191919)"
                      }}
                    >
                      {node.pvRight.toLocaleString()}
                    </strong>
                  </div>
                </div>
              </button>
            ))}
          </div>
        ))}
      </div>
    </div>
  );
};

export default OrganizationTreeCanvas;
