"""Utility helpers for rendering QA checklist data in FastAPI UI routes."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import json
import re
from html import escape as html_escape
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[3]
ACCESSIBILITY_CHECKLIST_PATH = PROJECT_ROOT / "docs" / "uiux" / "accessibility_qa_checklist.md"


@dataclass(frozen=True)
class ChecklistItem:
    """Individual checklist entry."""

    id: str
    text: str


@dataclass(frozen=True)
class ChecklistSection:
    """Group of related checklist entries."""

    id: str
    title: str
    items: list[ChecklistItem]


@dataclass(frozen=True)
class Checklist:
    """Top-level checklist semantics exposed to the HTTP layer."""

    id: str
    title: str
    version: str | None
    sections: list[ChecklistSection]
    source_path: str


def get_accessibility_checklist() -> Checklist:
    """Return the parsed accessibility QA checklist."""

    return _parse_accessibility_checklist()


@lru_cache(maxsize=1)
def _parse_accessibility_checklist() -> Checklist:
    if not ACCESSIBILITY_CHECKLIST_PATH.exists():
        raise FileNotFoundError(f"Checklist markdown not found: {ACCESSIBILITY_CHECKLIST_PATH}")

    markdown = ACCESSIBILITY_CHECKLIST_PATH.read_text(encoding="utf-8")
    title_line, *rest = markdown.splitlines()
    title, version = _extract_title_and_version(title_line)
    sections = _extract_sections("\n".join(rest))
    return Checklist(
        id="accessibility-qa",
        title=title,
        version=version,
        sections=sections,
        source_path=str(ACCESSIBILITY_CHECKLIST_PATH.relative_to(PROJECT_ROOT)),
    )


def serialize_checklist(checklist: Checklist) -> dict[str, Any]:
    """Serialize checklist dataclasses into a JSON-friendly dict."""

    return {
        "id": checklist.id,
        "title": checklist.title,
        "version": checklist.version,
        "source_path": checklist.source_path,
        "sections": [
            {
                "id": section.id,
                "title": section.title,
                "items": [{"id": item.id, "text": item.text} for item in section.items],
            }
            for section in checklist.sections
        ],
    }


def render_checklist_page_html(checklist: Checklist) -> str:
    """Render a lightweight HTML page for the checklist."""

    payload = serialize_checklist(checklist)
    payload_json = json.dumps(payload)
    title_text = html_escape(_build_page_title(payload))
    source_path = html_escape(payload["source_path"])

    return f"""<!DOCTYPE html>
<html lang="ko">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>{title_text}</title>
    <style>
      :root {{
        color-scheme: light dark;
        font-family: "Pretendard", "Spoqa Han Sans Neo", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        background: var(--page-bg, #0d1117);
        color: var(--page-fg, #e6edf3);
        --panel-bg: rgba(13, 17, 23, 0.8);
        --panel-border: rgba(240, 246, 252, 0.1);
        --accent: #2ea043;
        --accent-muted: rgba(46, 160, 67, 0.2);
        --muted: rgba(240, 246, 252, 0.6);
      }}

      body {{
        margin: 0;
        padding: 1.5rem;
        background: linear-gradient(180deg, rgba(13, 17, 27, 0.95), rgba(13, 17, 23, 0.95)),
          url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 20 20'%3E%3Cpath fill='rgba(46,160,67,0.08)' d='M0 0h10v10H0zM10 10h10v10H10z'/%3E%3C/svg%3E");
        min-height: 100vh;
      }}

      header {{
        max-width: 960px;
        margin: 0 auto 1.5rem;
        padding: 1.5rem;
        background: var(--panel-bg);
        border: 1px solid var(--panel-border);
        border-radius: 16px;
        backdrop-filter: blur(16px);
        box-shadow: 0 24px 36px rgba(10, 12, 18, 0.45);
      }}

      header h1 {{
        margin: 0 0 0.5rem;
        font-size: 1.75rem;
        letter-spacing: -0.02em;
      }}

      header p {{
        margin: 0;
        color: var(--muted);
      }}

      .checklist {{
        max-width: 960px;
        margin: 0 auto;
        display: grid;
        gap: 1.25rem;
      }}

      section {{
        background: rgba(13, 17, 23, 0.82);
        border: 1px solid var(--panel-border);
        border-radius: 18px;
        padding: 1.5rem;
        box-shadow: 0 16px 28px rgba(7, 10, 15, 0.4);
      }}

      section h2 {{
        margin: 0 0 1rem;
        font-size: 1.25rem;
        letter-spacing: -0.01em;
      }}

      ul {{
        list-style: none;
        padding: 0;
        margin: 0;
        display: grid;
        gap: 0.75rem;
      }}

      li {{
        display: flex;
        align-items: flex-start;
        gap: 0.75rem;
        padding: 0.75rem;
        border-radius: 12px;
        border: 1px solid transparent;
        background: rgba(13, 17, 23, 0.6);
        transition: border-color 0.2s ease, transform 0.2s ease;
      }}

      li:hover {{
        border-color: var(--accent-muted);
        transform: translateY(-2px);
      }}

      .item-label {{
        flex: 1;
        line-height: 1.5;
      }}

      .item-label code {{
        background: rgba(46, 160, 67, 0.12);
        padding: 0.1rem 0.35rem;
        border-radius: 6px;
        font-size: 0.9em;
      }}

      .item-label a {{
        color: #7ee787;
      }}

      input[type="checkbox"] {{
        width: 1.15rem;
        height: 1.15rem;
        accent-color: var(--accent);
        margin-top: 0.3rem;
      }}

      .toolbar {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 1.5rem;
        gap: 1rem;
      }}

      .toolbar button {{
        background: var(--accent);
        color: #0d1117;
        border: none;
        border-radius: 999px;
        padding: 0.6rem 1.4rem;
        font-weight: 600;
        cursor: pointer;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
        box-shadow: 0 15px 25px rgba(46, 160, 67, 0.25);
      }}

      .toolbar button:hover {{
        transform: translateY(-1px);
        box-shadow: 0 18px 32px rgba(46, 160, 67, 0.35);
      }}

      .toolbar button.secondary {{
        background: rgba(46, 160, 67, 0.16);
        color: var(--accent);
        box-shadow: none;
        border: 1px solid rgba(46, 160, 67, 0.4);
      }}

      .toolbar button.secondary:hover {{
        background: rgba(46, 160, 67, 0.24);
      }}

      .progress {{
        color: var(--muted);
        font-size: 0.95rem;
      }}

      footer {{
        max-width: 960px;
        margin: 2.5rem auto 0;
        color: var(--muted);
        font-size: 0.85rem;
        text-align: center;
      }}

      footer a {{
        color: #58a6ff;
      }}
    </style>
  </head>
  <body>
    <header>
      <div class="toolbar">
        <div>
          <h1>{title_text}</h1>
          <p id="progress" class="progress"></p>
        </div>
        <div>
          <button id="mark-all">모두 완료</button>
          <button id="reset-all" class="secondary">초기화</button>
        </div>
      </div>
      <p>체크 상태는 브라우저 Local Storage에 저장됩니다. 출처: <code>{source_path}</code></p>
    </header>
    <main class="checklist" id="checklist-root"></main>
    <footer>
      <p>AEG Hash QA 팀용 체크리스트 UI. 수정은 <code>{source_path}</code>를 업데이트하면 자동 반영됩니다.</p>
    </footer>
    <script>
      const CHECKLIST_DATA = {payload_json};
      const STORAGE_KEY = `qa-checklist::${{CHECKLIST_DATA.id}}::v${{CHECKLIST_DATA.version || "1"}}`;

      const root = document.getElementById("checklist-root");
      const progressEl = document.getElementById("progress");
      const markAllBtn = document.getElementById("mark-all");
      const resetAllBtn = document.getElementById("reset-all");

      function loadState() {{
        try {{
          const raw = localStorage.getItem(STORAGE_KEY);
          return raw ? JSON.parse(raw) : {{}};
        }} catch (error) {{
          console.warn("Failed to read checklist state", error);
          return {{}};
        }}
      }}

      function persistState(state) {{
        try {{
          localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
        }} catch (error) {{
          console.warn("Failed to persist checklist state", error);
        }}
      }}

      function render() {{
        const state = loadState();
        let total = 0;
        let completed = 0;

        root.innerHTML = "";
        CHECKLIST_DATA.sections.forEach((section) => {{
          const sectionEl = document.createElement("section");
          const heading = document.createElement("h2");
          heading.textContent = section.title;
          sectionEl.appendChild(heading);

          const list = document.createElement("ul");
          section.items.forEach((item) => {{
            const itemId = `${{section.id}}::${{item.id}}`;
            const isChecked = Boolean(state[itemId]);
            total += 1;
            if (isChecked) {{
              completed += 1;
            }}

            const li = document.createElement("li");
            const checkbox = document.createElement("input");
            checkbox.type = "checkbox";
            checkbox.id = itemId;
            checkbox.checked = isChecked;

            checkbox.addEventListener("change", () => {{
              const latest = loadState();
              latest[itemId] = checkbox.checked;
              if (!checkbox.checked) {{
                delete latest[itemId];
              }}
              persistState(latest);
              updateProgress();
            }});

            const label = document.createElement("label");
            label.htmlFor = itemId;
            label.className = "item-label";
            label.innerText = item.text;

            li.appendChild(checkbox);
            li.appendChild(label);
            list.appendChild(li);
          }});

          sectionEl.appendChild(list);
          root.appendChild(sectionEl);
        }});

        updateProgress(total, completed);
      }}

      function updateProgress(totalOverride, completedOverride) {{
        const state = loadState();
        let total = 0;
        let completed = 0;

        if (typeof totalOverride === "number" && typeof completedOverride === "number") {{
          total = totalOverride;
          completed = completedOverride;
        }} else {{
          CHECKLIST_DATA.sections.forEach((section) => {{
            section.items.forEach((item) => {{
              total += 1;
              const itemId = `${{section.id}}::${{item.id}}`;
              if (state[itemId]) {{
                completed += 1;
              }}
            }});
          }});
        }}

        const percent = total === 0 ? 0 : Math.round((completed / total) * 100);
        progressEl.textContent = `완료 ${{completed}} / ${{total}} · ${{percent}}%`;
      }}

      markAllBtn.addEventListener("click", () => {{
        const state = loadState();
        CHECKLIST_DATA.sections.forEach((section) => {{
          section.items.forEach((item) => {{
            const itemId = `${{section.id}}::${{item.id}}`;
            state[itemId] = true;
          }});
        }});
        persistState(state);
        render();
      }});

      resetAllBtn.addEventListener("click", () => {{
        if (confirm("체크 상태를 모두 초기화할까요?")) {{
          persistState({{}});
          render();
        }}
      }});

      render();
    </script>
  </body>
</html>"""


def _build_page_title(payload: dict[str, Any]) -> str:
    title = payload.get("title") or "QA Checklist"
    version = payload.get("version")
    return f"{title} ({version})" if version else title


TITLE_PATTERN = re.compile(r"#\s*(?P<title>.+?)(?:\s*\((?P<version>v[^)]+)\))?\s*$")
SECTION_PATTERN = re.compile(r"^##\s+(?P<title>.+)$", re.MULTILINE)
BULLET_PATTERN = re.compile(r"^[-*+]\s+(?P<text>.+)$")
ORDERED_PATTERN = re.compile(r"^\d+\.\s+(?P<text>.+)$")


def _extract_title_and_version(title_line: str) -> tuple[str, str | None]:
    match = TITLE_PATTERN.match(title_line.strip())
    if not match:
        return title_line.strip("# ").strip(), None
    return match.group("title").strip(), match.group("version")


def _extract_sections(markdown_body: str) -> list[ChecklistSection]:
    sections: list[ChecklistSection] = []
    matches = list(SECTION_PATTERN.finditer(markdown_body))
    for index, match in enumerate(matches):
        title = match.group("title").strip()
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(markdown_body)
        body = markdown_body[start:end].strip()
        items = _extract_items(body)
        if not items:
            continue
        sections.append(
            ChecklistSection(
                id=_slugify(title),
                title=title,
                items=[
                    ChecklistItem(id=_slugify(f"{title}-{idx}-{text}"), text=text)
                    for idx, text in enumerate(items, start=1)
                ],
            )
        )
    return sections


def _extract_items(body: str) -> list[str]:
    items: list[str] = []
    for line in body.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        bullet = BULLET_PATTERN.match(stripped)
        if bullet:
            items.append(bullet.group("text").strip())
            continue
        ordered = ORDERED_PATTERN.match(stripped)
        if ordered:
            items.append(ordered.group("text").strip())
            continue
    return items


SLUG_PATTERN = re.compile(r"[^a-z0-9]+")


def _slugify(text: str) -> str:
    slug = SLUG_PATTERN.sub("-", text.lower())
    slug = slug.strip("-")
    return slug or "item"
