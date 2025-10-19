#!/usr/bin/env python3
"""Export design tokens into CSS variables and Tailwind extend fragments."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, Tuple

ROOT = Path(__file__).resolve().parents[1]
TOKENS_DIR = ROOT / "tokens"
DIST_DIR = TOKENS_DIR / "dist"


def load_token_file(name: str) -> dict[str, Any]:
    path = TOKENS_DIR / f"{name}.json"
    if not path.exists():
        raise FileNotFoundError(f"Token file '{name}.json' not found (expected at {path})")
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def build_css_variables(
    colors: dict[str, Any], typography: dict[str, Any], components: dict[str, Any]
) -> str:
    lines = [":root {"]
    reference_map: dict[str, str] = {}

    def sanitize(name: str) -> str:
        return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")

    palette = colors.get("palette", {})
    for name, spec in palette.items():
        value = spec.get("value") if isinstance(spec, dict) else None
        if value:
            sanitized = sanitize(name)
            var_name = f"--aeg-color-{sanitized}"
            reference_map[f"colors.palette.{name}.value"] = var_name
            lines.append(f"  {var_name}: {value};")

    typography_support = colors.get("typography_support", {})
    for name, value in typography_support.items():
        sanitized = sanitize(name)
        var_name = f"--aeg-color-{sanitized}"
        reference_map[f"colors.typography_support.{name}"] = var_name
        lines.append(f"  {var_name}: {value};")

    elevation = colors.get("elevation", {})
    for name, value in elevation.items():
        sanitized = sanitize(name)
        var_name = f"--aeg-elevation-{sanitized}"
        reference_map[f"colors.elevation.{name}"] = var_name
        lines.append(f"  {var_name}: {value};")

    font_families = typography.get("font_families", {})
    for name, spec in font_families.items():
        value = spec.get("value") if isinstance(spec, dict) else None
        if value:
            sanitized = sanitize(name)
            var_name = f"--aeg-font-family-{sanitized}"
            reference_map[f"typography.font_families.{name}.value"] = var_name
            lines.append(f"  {var_name}: {value};")

    scale = typography.get("scale", {})
    for name, spec in scale.items():
        for key, value in spec.items():
            sanitized = sanitize(f"{name}-{key}")
            var_name = f"--aeg-typography-{sanitized}"
            reference_map[f"typography.scale.{name}.{key}"] = var_name
            lines.append(f"  {var_name}: {value};")

    token_pattern = re.compile(r"\{([^{}]+)\}")

    def normalize_value(raw: Any) -> Tuple[Any, bool]:
        if not isinstance(raw, str):
            return raw, True

        if raw.startswith("{") and raw.endswith("}") and raw.count("{") == 1:
            token_path = raw[1:-1]
            var_name = reference_map.get(token_path)
            if var_name:
                return f"var({var_name})", True
            return raw, False

        def replace(match: re.Match[str]) -> str:
            token_path = match.group(1)
            var_name = reference_map.get(token_path)
            if not var_name:
                return match.group(0)
            return f"var({var_name})"

        replaced = token_pattern.sub(replace, raw)
        if "{" in replaced or "}" in replaced:
            return replaced, False
        return replaced, True

    def flatten_component(prefix: Tuple[str, ...], data: Dict[str, Any]) -> None:
        for key, value in data.items():
            sanitized_key = sanitize(key)
            next_prefix = prefix + (sanitized_key,)
            if isinstance(value, dict):
                flatten_component(next_prefix, value)
            else:
                normalized, include = normalize_value(value)
                if not include:
                    continue
                var_name = "--aeg-component-" + "-".join(next_prefix)
                lines.append(f"  {var_name}: {normalized};")

    for name, spec in components.get("components", {}).items():
        if isinstance(spec, dict):
            flatten_component((sanitize(name),), spec)

    lines.append("}")
    lines.append("")
    return "\n".join(lines)


def build_tailwind_extend(
    colors: dict[str, Any], typography: dict[str, Any], components: dict[str, Any]
) -> dict[str, Any]:
    palette = {
        name: spec.get("value")
        for name, spec in colors.get("palette", {}).items()
        if isinstance(spec, dict) and spec.get("value")
    }
    palette.update(
        {
            name.replace("text.", "text-"): value
            for name, value in colors.get("typography_support", {}).items()
        }
    )

    elevation = colors.get("elevation", {})

    font_families = {
        name.replace("_", "-"): spec.get("value")
        for name, spec in typography.get("font_families", {}).items()
        if isinstance(spec, dict) and spec.get("value")
    }

    font_sizes: dict[str, Any] = {}
    for name, spec in typography.get("scale", {}).items():
        size = spec.get("font_size")
        if not size:
            continue
        options = {
            "lineHeight": spec.get("line_height"),
            "letterSpacing": spec.get("letter_spacing"),
        }
        options = {k: v for k, v in options.items() if v is not None}
        font_sizes[name.replace("_", "-")] = [size, options]

    border_radius = {}
    button_radius = components.get("components", {}).get("button", {}).get("border_radius")
    if button_radius:
        border_radius["button"] = button_radius
    card_radius = components.get("components", {}).get("card", {}).get("border_radius")
    if card_radius:
        border_radius["card"] = card_radius

    box_shadow = {
        f"aeg-{name.replace('_', '-')}": value for name, value in elevation.items() if value
    }

    return {
        "colors": palette,
        "fontFamily": font_families,
        "fontSize": font_sizes,
        "borderRadius": border_radius,
        "boxShadow": box_shadow,
    }


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def main() -> None:
    colors = load_token_file("colors")
    typography = load_token_file("typography")
    components = load_token_file("components")

    css_variables = build_css_variables(colors, typography, components)
    write_file(DIST_DIR / "design-tokens.css", css_variables)

    tailwind_extend = build_tailwind_extend(colors, typography, components)
    tailwind_content = (
        "module.exports = {\n"
        "  theme: {\n"
        "    extend: "
        + json.dumps(tailwind_extend, indent=4)
        + "\n"
        "  }\n"
        "};\n"
    )
    write_file(DIST_DIR / "tailwind.tokens.cjs", tailwind_content)

    print("Design token exports generated:")
    print(f" - {DIST_DIR / 'design-tokens.css'}")
    print(f" - {DIST_DIR / 'tailwind.tokens.cjs'}")


if __name__ == "__main__":
    main()
