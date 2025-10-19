import React from "react";
import Button from "../Button";

export type MiningAssetStatus = "healthy" | "warning" | "critical";

export interface MiningAssetCard {
  asset: string;
  hashRate: string;
  rejectionRate: string;
  dailyProfit: string;
  status: MiningAssetStatus;
  lastUpdated: string;
}

export interface MiningDashboardProps {
  totalHashPower: string;
  totalDailyProfit: string;
  activeAlerts: number;
  pendingWithdrawals: number;
  assets: MiningAssetCard[];
  onRefresh?: () => void;
  onSelectAsset?: (asset: string) => void;
}

const statusLabel: Record<MiningAssetStatus, string> = {
  healthy: "정상",
  warning: "주의",
  critical: "위험"
};

const statusColors: Record<MiningAssetStatus, string> = {
  healthy: "var(--aeg-colors-feedback-success-background, #e6f6e5)",
  warning: "var(--aeg-colors-feedback-warning-background, #fff7e0)",
  critical: "var(--aeg-colors-feedback-error-background, #fdecea)"
};

const statusTextColors: Record<MiningAssetStatus, string> = {
  healthy: "var(--aeg-colors-feedback-success-foreground, #206530)",
  warning: "var(--aeg-colors-feedback-warning-foreground, #805b10)",
  critical: "var(--aeg-colors-feedback-error-foreground, #b22222)"
};

const cardStyle: React.CSSProperties = {
  borderRadius: "16px",
  border: "1px solid var(--aeg-colors-border-subtle, #e4e6eb)",
  background: "var(--aeg-colors-surface-primary, #ffffff)",
  padding: "20px",
  boxShadow: "var(--aeg-component-card-shadow, 0 8px 20px rgba(15, 23, 42, 0.08))",
  display: "flex",
  flexDirection: "column",
  gap: "12px"
};

export const MiningDashboard: React.FC<MiningDashboardProps> = ({
  totalHashPower,
  totalDailyProfit,
  activeAlerts,
  pendingWithdrawals,
  assets,
  onRefresh,
  onSelectAsset
}) => {
  return (
    <section
      aria-label="채굴 현황 대시보드"
      style={{
        display: "flex",
        flexDirection: "column",
        gap: "24px",
        maxWidth: "1120px",
        margin: "0 auto"
      }}
    >
      <header
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          gap: "16px",
          flexWrap: "wrap"
        }}
      >
        <div>
          <h2
            style={{
              margin: 0,
              fontSize: "var(--aeg-typography-title-font-size, 24px)",
              lineHeight: "1.4"
            }}
          >
            채굴 요약
          </h2>
          <p
            style={{
              margin: "4px 0 0",
              color: "var(--aeg-colors-text-subtle, #4b5563)"
            }}
          >
            8종 자산 채굴 현황과 출금 상태를 확인하세요.
          </p>
        </div>
        <Button onClick={onRefresh}>데이터 새로고침</Button>
      </header>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))",
          gap: "16px"
        }}
      >
        <article style={cardStyle} aria-label="총 해시 파워">
          <span
            style={{
              fontSize: "var(--aeg-typography-overline-font-size, 12px)",
              letterSpacing: "0.08em",
              textTransform: "uppercase",
              color: "var(--aeg-colors-text-subtle, #4b5563)"
            }}
          >
            총 해시 파워
          </span>
          <strong
            style={{
              fontSize: "32px",
              lineHeight: 1.2,
              color: "var(--aeg-colors-text-primary, #0f172a)"
            }}
          >
            {totalHashPower}
          </strong>
          <p
            style={{
              margin: 0,
              color: "var(--aeg-colors-text-muted, #6b7280)"
            }}
          >
            최신 데이터 기준 수집된 총 해시 파워입니다.
          </p>
        </article>

        <article style={cardStyle} aria-label="일일 채굴 수익">
          <span
            style={{
              fontSize: "var(--aeg-typography-overline-font-size, 12px)",
              letterSpacing: "0.08em",
              textTransform: "uppercase",
              color: "var(--aeg-colors-text-subtle, #4b5563)"
            }}
          >
            일일 채굴 수익
          </span>
          <strong
            style={{
              fontSize: "32px",
              lineHeight: 1.2,
              color: "var(--aeg-colors-text-primary, #0f172a)"
            }}
          >
            {totalDailyProfit}
          </strong>
          <p
            style={{
              margin: 0,
              color: "var(--aeg-colors-text-muted, #6b7280)"
            }}
          >
            전일 대비 변화와 위험 경고를 확인하세요.
          </p>
        </article>

        <article style={cardStyle} aria-label="활성 경보">
          <span
            style={{
              fontSize: "var(--aeg-typography-overline-font-size, 12px)",
              letterSpacing: "0.08em",
              textTransform: "uppercase",
              color: "var(--aeg-colors-text-subtle, #4b5563)"
            }}
          >
            활성 경보
          </span>
          <div
            style={{
              display: "flex",
              alignItems: "baseline",
              gap: "8px"
            }}
          >
            <strong
              style={{
                fontSize: "32px",
                color: "var(--aeg-colors-text-primary, #0f172a)"
              }}
            >
              {activeAlerts}
            </strong>
            <span
              style={{
                fontSize: "14px",
                color: "var(--aeg-colors-text-muted, #6b7280)"
              }}
            >
              건
            </span>
          </div>
          <p
            style={{
              margin: 0,
              color: "var(--aeg-colors-text-muted, #6b7280)"
            }}
          >
            거절율 상승, API 실패 등 즉시 조치가 필요한 항목 수.
          </p>
        </article>

        <article style={cardStyle} aria-label="출금 대기">
          <span
            style={{
              fontSize: "var(--aeg-typography-overline-font-size, 12px)",
              letterSpacing: "0.08em",
              textTransform: "uppercase",
              color: "var(--aeg-colors-text-subtle, #4b5563)"
            }}
          >
            출금 대기
          </span>
          <div
            style={{
              display: "flex",
              alignItems: "baseline",
              gap: "8px"
            }}
          >
            <strong
              style={{
                fontSize: "32px",
                color: "var(--aeg-colors-text-primary, #0f172a)"
              }}
            >
              {pendingWithdrawals}
            </strong>
            <span
              style={{
                fontSize: "14px",
                color: "var(--aeg-colors-text-muted, #6b7280)"
              }}
            >
              건
            </span>
          </div>
          <p
            style={{
              margin: 0,
              color: "var(--aeg-colors-text-muted, #6b7280)"
            }}
          >
            승인 대기 중인 HashDam 출금 요청 수를 알려줍니다.
          </p>
        </article>
      </div>

      <section aria-label="채굴 자산 리스트" style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
        <header style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <h3
            style={{
              margin: 0,
              fontSize: "var(--aeg-typography-subtitle-font-size, 18px)",
              color: "var(--aeg-colors-text-primary, #0f172a)"
            }}
          >
            자산별 상세
          </h3>
          <span style={{ color: "var(--aeg-colors-text-subtle, #4b5563)", fontSize: "14px" }}>
            8종 자산의 해시율과 거절율을 실시간으로 보여줍니다.
          </span>
        </header>

        <div
          role="list"
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))",
            gap: "16px"
          }}
        >
          {assets.map((asset) => (
            <article
              key={asset.asset}
              role="listitem"
              onClick={() => onSelectAsset?.(asset.asset)}
              style={{
                ...cardStyle,
                cursor: onSelectAsset ? "pointer" : "default",
                outline: "none"
              }}
              tabIndex={onSelectAsset ? 0 : undefined}
              onKeyDown={(event) => {
                if ((event.key === "Enter" || event.key === " ") && onSelectAsset) {
                  event.preventDefault();
                  onSelectAsset(asset.asset);
                }
              }}
              aria-label={`${asset.asset} 자산 카드`}
            >
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <strong
                  style={{
                    fontSize: "20px",
                    color: "var(--aeg-colors-text-primary, #0f172a)"
                  }}
                >
                  {asset.asset}
                </strong>
                <span
                  style={{
                    padding: "4px 10px",
                    borderRadius: "999px",
                    backgroundColor: statusColors[asset.status],
                    color: statusTextColors[asset.status],
                    fontSize: "12px",
                    fontWeight: 600
                  }}
                >
                  {statusLabel[asset.status]}
                </span>
              </div>
              <dl
                style={{
                  display: "grid",
                  gridTemplateColumns: "repeat(2, minmax(0, 1fr))",
                  rowGap: "8px",
                  columnGap: "12px",
                  margin: 0
                }}
              >
                <dt
                  style={{
                    fontSize: "12px",
                    color: "var(--aeg-colors-text-subtle, #4b5563)",
                    textTransform: "uppercase",
                    letterSpacing: "0.05em"
                  }}
                >
                  해시율
                </dt>
                <dd
                  style={{
                    margin: 0,
                    fontSize: "16px",
                    color: "var(--aeg-colors-text-primary, #0f172a)"
                  }}
                >
                  {asset.hashRate}
                </dd>
                <dt
                  style={{
                    fontSize: "12px",
                    color: "var(--aeg-colors-text-subtle, #4b5563)",
                    textTransform: "uppercase",
                    letterSpacing: "0.05em"
                  }}
                >
                  거절율
                </dt>
                <dd
                  style={{
                    margin: 0,
                    fontSize: "16px",
                    color: "var(--aeg-colors-text-primary, #0f172a)"
                  }}
                >
                  {asset.rejectionRate}
                </dd>
                <dt
                  style={{
                    fontSize: "12px",
                    color: "var(--aeg-colors-text-subtle, #4b5563)",
                    textTransform: "uppercase",
                    letterSpacing: "0.05em"
                  }}
                >
                  일일 수익
                </dt>
                <dd
                  style={{
                    margin: 0,
                    fontSize: "16px",
                    color: "var(--aeg-colors-text-primary, #0f172a)"
                  }}
                >
                  {asset.dailyProfit}
                </dd>
              </dl>
              <p
                style={{
                  margin: 0,
                  fontSize: "12px",
                  color: "var(--aeg-colors-text-muted, #6b7280)"
                }}
              >
                최근 동기화: {asset.lastUpdated}
              </p>
            </article>
          ))}
        </div>
      </section>
    </section>
  );
};

export default MiningDashboard;

