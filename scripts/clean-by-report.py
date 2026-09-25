#!/usr/bin/env python3
"""按 ktlint 报告中的 “Unused/Unnecessary import” 精确行号删除对应 import 行。

用法:
    python scripts/clean-by-report.py --report <ktlintKotlinSourceCheck.txt> --src-root <模块根(app)> [--apply]

report 中的路径形如 src/main/java/...，相对 --src-root 解析。
"""

from __future__ import annotations

import argparse
import re
from collections import defaultdict
from pathlib import Path

LINE_RE = re.compile(r"^(src/main/java/[\w/]+\.kt):(\d+):\d+: (?:Unused|Unnecessary) import")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--report", required=True)
    ap.add_argument("--src-root", required=True, help="containing src/main/java, e.g. app/")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    root = Path(args.src_root).resolve()
    targets: dict[Path, list[int]] = defaultdict(list)
    for line in Path(args.report).read_text(encoding="utf-8", errors="ignore").split("\n"):
        m = LINE_RE.match(line.strip())
        if m:
            targets[root / m.group(1)].append(int(m.group(2)))

    changed = 0
    removed = 0
    for path, lines_to_remove in targets.items():
        if not path.exists():
            print(f"  missing: {path}")
            continue
        lines = path.read_text(encoding="utf-8").split("\n")
        before = len(lines)
        for ln in sorted(set(lines_to_remove), reverse=True):
            idx = ln - 1
            if 0 <= idx < len(lines) and lines[idx].strip().startswith("import "):
                del lines[idx]
                removed += 1
        if len(lines) != before:
            changed += 1
            if args.apply:
                path.write_text("\n".join(lines), encoding="utf-8")

    mode = "APPLIED" if args.apply else "DRY-RUN"
    print(f"[{mode}] files: {changed}; import lines removed: {removed}")


if __name__ == "__main__":
    main()
