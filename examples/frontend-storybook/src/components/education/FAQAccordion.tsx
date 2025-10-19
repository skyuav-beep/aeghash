import React, { useState } from "react";

export interface FAQItem {
  question: string;
  answer: string;
  category: string;
}

export interface FAQAccordionProps {
  items: FAQItem[];
  defaultOpenIndex?: number;
}

export const FAQAccordion: React.FC<FAQAccordionProps> = ({ items, defaultOpenIndex = 0 }) => {
  const [openIndex, setOpenIndex] = useState<number | null>(defaultOpenIndex);

  return (
    <section
      aria-label="FAQ"
      className="aeg-faq-accordion"
      style={{
        borderRadius: "16px",
        border: "1px solid var(--aeg-colors-border-subtle, #e4e6eb)",
        background: "var(--aeg-colors-surface-primary, #ffffff)",
        padding: "8px",
        display: "flex",
        flexDirection: "column",
        gap: "8px"
      }}
    >
      {items.map((item, index) => {
        const isOpen = index === openIndex;
        return (
          <article
            key={item.question}
            style={{
              borderRadius: "12px",
              border: "1px solid var(--aeg-colors-border-muted, #d1d5db)",
              overflow: "hidden",
              background: isOpen
                ? "var(--aeg-colors-surface-emphasis, #f8fafc)"
                : "var(--aeg-colors-surface-primary, #ffffff)",
              transition: "background 120ms ease"
            }}
          >
            <button
              onClick={() => setOpenIndex(isOpen ? null : index)}
              style={{
                all: "unset",
                display: "flex",
                flexDirection: "column",
                gap: "4px",
                width: "100%",
                padding: "16px",
                cursor: "pointer"
              }}
              aria-expanded={isOpen}
              aria-controls={`faq-panel-${index}`}
            >
              <span
                style={{
                  fontSize: "12px",
                  textTransform: "uppercase",
                  letterSpacing: "0.06em",
                  color: "var(--aeg-colors-text-subtle, #4b5563)"
                }}
              >
                {item.category}
              </span>
              <strong
                style={{
                  fontSize: "var(--aeg-typography-body-primary-font-size, 16px)",
                  color: "var(--aeg-colors-text-primary, #0f172a)",
                  lineHeight: 1.5
                }}
              >
                {item.question}
              </strong>
            </button>
            {isOpen ? (
              <div
                id={`faq-panel-${index}`}
                style={{
                  padding: "0 16px 16px",
                  color: "var(--aeg-colors-text-muted, #6b7280)",
                  fontSize: "15px",
                  lineHeight: 1.6
                }}
              >
                {item.answer}
              </div>
            ) : null}
          </article>
        );
      })}
    </section>
  );
};

export default FAQAccordion;

