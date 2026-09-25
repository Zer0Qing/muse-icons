#!/usr/bin/env python3
"""Muse Icons -> Android VectorDrawable 生成器。

将 icons.json 中的 SVG 元素（path / circle / rect / ellipse，含 rotate transform）
转换为 VectorDrawable XML（24dp，stroke 1.7 圆头圆角，strokeColor=#FF000000 供 Compose tint）。

用法:
    python scripts/to-vector.py --out <drawable 目录> [--prefix ic_muse_]
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

TEMPLATE = (
    '<?xml version="1.0" encoding="utf-8"?>\n'
    '<vector xmlns:android="http://schemas.android.com/apk/res/android"\n'
    '    android:width="24dp"\n'
    '    android:height="24dp"\n'
    '    android:viewportWidth="24"\n'
    '    android:viewportHeight="24">\n'
    "{body}"
    "</vector>\n"
)


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


def path_xml(d: str, indent: str = "    ") -> str:
    return (
        f"{indent}<path\n"
        f'{indent}    android:pathData="{d}"\n'
        f'{indent}    android:strokeColor="#FF000000"\n'
        f'{indent}    android:strokeWidth="1.7"\n'
        f'{indent}    android:strokeLineCap="round"\n'
        f'{indent}    android:strokeLineJoin="round" />\n'
    )


def convert(name: str, body: str) -> str:
    parts: list[str] = []
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
            if not tm:  # pragma: no cover - 防御：未知 transform 原样报出
                raise ValueError(f"{name}: unsupported transform {transform}")
            angle, px, py = tm.group(1), tm.group(2), tm.group(3)
            parts.append(
                f'    <group android:rotation="{n(float(angle))}"'
                f' android:pivotX="{n(float(px))}" android:pivotY="{n(float(py))}">\n'
            )
            parts.append(path_xml(d, indent="        "))
            parts.append("    </group>\n")
        else:
            parts.append(path_xml(d))
    return "".join(parts)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True, help="drawable output directory")
    parser.add_argument("--prefix", default="ic_muse_")
    args = parser.parse_args()

    icons = json.loads((ROOT / "icons.json").read_text(encoding="utf-8"))
    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)

    for name, body in icons.items():
        xml = TEMPLATE.format(body=convert(name, body))
        file_name = f"{args.prefix}{name.replace('-', '_')}.xml"
        (out / file_name).write_text(xml, encoding="utf-8")

    print(f"wrote {len(icons)} vector drawables -> {out}")


if __name__ == "__main__":
    main()
