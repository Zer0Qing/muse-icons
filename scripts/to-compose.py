#!/usr/bin/env python3
"""Muse Icons -> Compose ImageVector (MuseIcons.kt) 生成器（静态版）。

生成 ``object MuseIcons { val search: ImageVector by lazy { ... } }``。
使用 ImageVector.Builder.addPath(pathData = addPathNodes(...)) 承载路径，
非 Composable、可在任意上下文使用（与 TablerIcons.Search 同构）。

用法:
    python scripts/to-compose.py --out <MuseIcons.kt 路径>
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

ELEM_RE = re.compile(r"<(circle|rect|ellipse|path)\s+([^>]*?)/>")
ATTR_RE = re.compile(r"([a-zA-Z]+)='([^']*)'")
TRANSFORM_RE = re.compile(r"rotate\((-?[\d.]+)\s+([\d.]+)\s+([\d.]+)\)")

HEADER = """@file:Suppress("LargeClass")

package io.zer0.muse.ui.common.icons

import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.SolidColor
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.StrokeJoin
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.graphics.vector.addPathNodes
import androidx.compose.ui.graphics.vector.group
import androidx.compose.ui.unit.dp

/**
 * Muse Icons — 自绘图标集的 Compose ImageVector 版本（静态,非 Composable）。
 *
 * 由 muse-icons/scripts/to-compose.py 自动生成，勿手改。
 * 源: https://github.com/Zer0Qing/muse-icons
 */
object MuseIcons {
"""

FOOTER = "}\n"

KOTLIN_KEYWORDS = {
    "package", "is", "in", "object", "class", "fun", "val", "var", "when",
    "if", "else", "for", "while", "return", "as", "break", "continue",
}


def parse_attrs(raw: str) -> dict:
    return {m.group(1): m.group(2) for m in ATTR_RE.finditer(raw)}


def n(v: float) -> str:
    s = f"{v:.4f}".rstrip("0").rstrip(".")
    return s if s else "0"


def circle_to_path(a: dict) -> str:
    cx, cy, r = float(a["cx"]), float(a["cy"]), float(a["r"])
    return (
        f"M{n(cx - r)} {n(cy)}"
        f"a{n(r)} {n(r)} 0 1 0 {n(2 * r)} 0"
        f"a{n(r)} {n(r)} 0 1 0 {n(-2 * r)} 0"
    )


def rect_to_path(a: dict) -> str:
    x, y = float(a["x"]), float(a["y"])
    w, h = float(a["width"]), float(a["height"])
    rx = float(a.get("rx", 0))
    if rx <= 0:
        return f"M{n(x)} {n(y)}h{n(w)}v{n(h)}h{n(-w)}z"
    return (
        f"M{n(x + rx)} {n(y)}"
        f"h{n(w - 2 * rx)}"
        f"a{n(rx)} {n(rx)} 0 0 1 {n(rx)} {n(rx)}"
        f"v{n(h - 2 * rx)}"
        f"a{n(rx)} {n(rx)} 0 0 1 {n(-rx)} {n(rx)}"
        f"h{n(-(w - 2 * rx))}"
        f"a{n(rx)} {n(rx)} 0 0 1 {n(-rx)} {n(-rx)}"
        f"v{n(-(h - 2 * rx))}"
        f"a{n(rx)} {n(rx)} 0 0 1 {n(rx)} {n(-rx)}"
        f"z"
    )


def ellipse_to_path(a: dict) -> str:
    cx, cy = float(a["cx"]), float(a["cy"])
    rx, ry = float(a["rx"]), float(a["ry"])
    return (
        f"M{n(cx - rx)} {n(cy)}"
        f"a{n(rx)} {n(ry)} 0 1 0 {n(2 * rx)} 0"
        f"a{n(rx)} {n(ry)} 0 1 0 {n(-2 * rx)} 0"
    )


def kotlin_string(s: str, indent: str, chunk: int = 80) -> str:
    """超长字符串拆成多段拼接（第二段起缩进 +4），避免 max-line-length。"""
    parts = [s[i : i + chunk] for i in range(0, len(s), chunk)]
    line = f'{indent}"{parts[0]}"'
    for p in parts[1:]:
        line += f' +\n{indent}    "{p}"'
    return line


def path_call(d: str, indent: str) -> str:
    single = f'{indent}    pathData = addPathNodes("{d}"),'
    if len(single) <= 120:
        path_data = single + "\n"
    else:
        str_line = kotlin_string(d, f"{indent}            ")
        path_data = (
            f"{indent}    pathData =\n"
            f"{indent}        addPathNodes(\n"
            f"{str_line},\n"
            f"{indent}        ),\n"
        )
    return (
        f"{indent}addPath(\n"
        + path_data
        + f"{indent}    stroke = SolidColor(Color(0xFF000000)),\n"
        f"{indent}    strokeLineWidth = 1.7f,\n"
        f"{indent}    strokeLineCap = StrokeCap.Round,\n"
        f"{indent}    strokeLineJoin = StrokeJoin.Round,\n"
        f"{indent})\n"
    )


def camel(name: str) -> str:
    parts = name.replace("-", "_").split("_")
    fn = parts[0] + "".join(p.capitalize() for p in parts[1:])
    if fn in KOTLIN_KEYWORDS:
        fn += "Icon"
    return fn


def convert_icon(name: str, body: str) -> str:
    body_parts: list[str] = []
    for m in ELEM_RE.finditer(body):
        tag, raw = m.group(1), m.group(2)
        a = parse_attrs(raw)
        if tag == "circle":
            d = circle_to_path(a)
        elif tag == "rect":
            d = rect_to_path(a)
        elif tag == "ellipse":
            d = ellipse_to_path(a)
        else:
            d = a["d"]
        transform = a.get("transform")
        if transform:
            tm = TRANSFORM_RE.search(transform)
            if not tm:  # pragma: no cover
                raise ValueError(f"{name}: unsupported transform {transform}")
            angle, px, py = tm.group(1), tm.group(2), tm.group(3)
            body_parts.append(
                f"            group(\n"
                f"                rotate = {n(float(angle))}f,\n"
                f"                pivotX = {n(float(px))}f,\n"
                f"                pivotY = {n(float(py))}f,\n"
                f"            ) {{\n"
            )
            body_parts.append(path_call(d, indent="                "))
            body_parts.append("            }\n")
        else:
            body_parts.append(path_call(d, indent="            "))

    val = camel(name)
    out: list[str] = []
    out.append(f"    /** {name} */\n")
    out.append(f"    val {val}: ImageVector by lazy {{\n")
    out.append("        ImageVector.Builder(\n")
    out.append(f'            name = "{name}",\n')
    out.append("            defaultWidth = 24.dp,\n")
    out.append("            defaultHeight = 24.dp,\n")
    out.append("            viewportWidth = 24f,\n")
    out.append("            viewportHeight = 24f,\n")
    out.append("        ).apply {\n")
    out.extend(body_parts)
    out.append("        }.build()\n")
    out.append("    }\n\n")
    return "".join(out)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True, help="MuseIcons.kt output path")
    args = parser.parse_args()

    icons = json.loads((ROOT / "icons.json").read_text(encoding="utf-8"))
    out_path = Path(args.out).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    parts = [HEADER]
    for name, body in icons.items():
        parts.append(convert_icon(name, body))
    parts.append(FOOTER)
    text = "".join(parts).replace("\n\n}\n", "\n}\n")
    out_path.write_text(text, encoding="utf-8")
    print(f"wrote {len(icons)} static icons -> {out_path}")


if __name__ == "__main__":
    main()
