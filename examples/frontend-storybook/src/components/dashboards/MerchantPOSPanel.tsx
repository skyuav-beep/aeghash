import React from "react";
import Button from "../Button";

export interface TransactionItem {
  id: string;
  amount: string;
  status: "completed" | "pending" | "refunded";
  timestamp: string;
}

export interface StaffRole {
  name: string;
  role: "manager" | "cashier";
  permissions: string[];
  invitedAt: string;
}

export interface MerchantPOSPanelProps {
  storeName: string;
  qrUrl: string;
  currencyLabel: string;
  amount: string;
  statusMessage: string;
  transactions: TransactionItem[];
  staff: StaffRole[];
  onGenerateQr?: () => void;
  onRefund?: (transactionId: string) => void;
  onInviteStaff?: () => void;
}

const panelStyle: React.CSSProperties = {
  display: "grid",
  gap: "24px",
  gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))",
  alignItems: "start"
};

const sectionStyle: React.CSSProperties = {
  borderRadius: "16px",
  border: "1px solid var(--aeg-colors-border-subtle, #e4e6eb)",
  background: "var(--aeg-colors-surface-primary, #ffffff)",
  padding: "24px",
  boxShadow: "var(--aeg-component-card-shadow, 0 8px 20px rgba(15, 23, 42, 0.08))",
  display: "flex",
  flexDirection: "column",
  gap: "16px"
};

const badgeColors: Record<TransactionItem["status"], string> = {
  completed: "var(--aeg-colors-feedback-success-background, #e6f6e5)",
  pending: "var(--aeg-colors-feedback-warning-background, #fff7e0)",
  refunded: "var(--aeg-colors-feedback-info-background, #e4f0ff)"
};

const badgeText: Record<TransactionItem["status"], string> = {
  completed: "완료",
  pending: "대기",
  refunded: "환불"
};

export const MerchantPOSPanel: React.FC<MerchantPOSPanelProps> = ({
  storeName,
  qrUrl,
  currencyLabel,
  amount,
  statusMessage,
  transactions,
  staff,
  onGenerateQr,
  onRefund,
  onInviteStaff
}) => {
  return (
    <section aria-label="가맹점 POS 및 QR 패널" style={panelStyle}>
      <article aria-label="QR 결제 생성" style={sectionStyle}>
        <header>
          <h2
            style={{
              margin: 0,
              fontSize: "var(--aeg-typography-subtitle-font-size, 20px)",
              color: "var(--aeg-colors-text-primary, #0f172a)"
            }}
          >
            {storeName} · QR 결제
          </h2>
          <p style={{ margin: "8px 0 0", color: "var(--aeg-colors-text-subtle, #4b5563)" }}>
            매장 결제 금액을 입력하고 QR을 생성하세요.
          </p>
        </header>

        <label style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
          <span style={{ fontSize: "14px", color: "var(--aeg-colors-text-muted, #6b7280)" }}>
            결제 금액 ({currencyLabel})
          </span>
          <div
            style={{
              borderRadius: "12px",
              border: "1px solid var(--aeg-colors-border-strong, #cbd2e1)",
              padding: "16px",
              fontSize: "24px",
              fontWeight: 600,
              color: "var(--aeg-colors-text-primary, #0f172a)"
            }}
            aria-live="polite"
          >
            {amount}
          </div>
        </label>

        <Button onClick={onGenerateQr}>QR 생성</Button>

        <div
          style={{
            borderRadius: "16px",
            overflow: "hidden",
            border: "1px dashed var(--aeg-colors-border-subtle, #d1d5db)",
            background: "var(--aeg-colors-surface-muted, #f8fafc)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            minHeight: "200px"
          }}
        >
          <img
            src={qrUrl}
            alt={`${storeName} 결제 QR`}
            style={{ width: "160px", height: "160px", objectFit: "contain" }}
          />
        </div>

        <p style={{ margin: 0, color: "var(--aeg-colors-text-subtle, #4b5563)" }}>{statusMessage}</p>
      </article>

      <article aria-label="결제 내역" style={sectionStyle}>
        <header style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <h3
            style={{
              margin: 0,
              fontSize: "var(--aeg-typography-subtitle-font-size, 18px)",
              color: "var(--aeg-colors-text-primary, #0f172a)"
            }}
          >
            최근 결제 내역
          </h3>
          <span style={{ fontSize: "14px", color: "var(--aeg-colors-text-muted, #6b7280)" }}>
            최근 10건을 표시합니다.
          </span>
        </header>
        <ul style={{ listStyle: "none", margin: 0, padding: 0, display: "flex", flexDirection: "column", gap: "12px" }}>
          {transactions.map((transaction) => (
            <li
              key={transaction.id}
              style={{
                display: "grid",
                gridTemplateColumns: "1fr auto",
                gap: "12px",
                alignItems: "center",
                padding: "12px 16px",
                borderRadius: "12px",
                border: "1px solid var(--aeg-colors-border-subtle, #e4e6eb)"
              }}
            >
              <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
                <strong style={{ color: "var(--aeg-colors-text-primary, #0f172a)" }}>{transaction.amount}</strong>
                <span style={{ fontSize: "12px", color: "var(--aeg-colors-text-muted, #6b7280)" }}>
                  {transaction.timestamp}
                </span>
              </div>
              <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <span
                  style={{
                    padding: "4px 10px",
                    borderRadius: "999px",
                    background: badgeColors[transaction.status],
                    fontSize: "12px",
                    fontWeight: 600,
                    color: "var(--aeg-colors-text-primary, #0f172a)"
                  }}
                >
                  {badgeText[transaction.status]}
                </span>
                {transaction.status === "completed" ? (
                  <Button
                    variant="secondary"
                    onClick={() => onRefund?.(transaction.id)}
                    style={{ fontSize: "12px", padding: "8px 12px" }}
                  >
                    환불
                  </Button>
                ) : null}
              </div>
            </li>
          ))}
        </ul>
      </article>

      <article aria-label="직원 권한" style={sectionStyle}>
        <header style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <h3
            style={{
              margin: 0,
              fontSize: "var(--aeg-typography-subtitle-font-size, 18px)",
              color: "var(--aeg-colors-text-primary, #0f172a)"
            }}
          >
            직원 권한 관리
          </h3>
          <Button variant="secondary" onClick={onInviteStaff}>
            초대 보내기
          </Button>
        </header>
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead>
            <tr style={{ textAlign: "left", color: "var(--aeg-colors-text-subtle, #4b5563)", fontSize: "12px" }}>
              <th style={{ padding: "8px 0" }}>이름</th>
              <th style={{ padding: "8px 0" }}>역할</th>
              <th style={{ padding: "8px 0" }}>권한</th>
              <th style={{ padding: "8px 0" }}>초대일</th>
            </tr>
          </thead>
          <tbody>
            {staff.map((member) => (
              <tr
                key={member.name}
                style={{
                  borderTop: "1px solid var(--aeg-colors-border-subtle, #e4e6eb)",
                  color: "var(--aeg-colors-text-primary, #0f172a)"
                }}
              >
                <td style={{ padding: "12px 0" }}>{member.name}</td>
                <td style={{ padding: "12px 0", textTransform: "capitalize" }}>
                  {member.role === "manager" ? "점장" : "캐셔"}
                </td>
                <td style={{ padding: "12px 0" }}>
                  {member.permissions.join(", ")}
                </td>
                <td style={{ padding: "12px 0", color: "var(--aeg-colors-text-muted, #6b7280)" }}>
                  {member.invitedAt}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </article>
    </section>
  );
};

export default MerchantPOSPanel;

