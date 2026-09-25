#!/usr/bin/env python3
"""保守清理 Kotlin 文件的 “完全未使用 import”。

仅当 import 的末段符号在文件正文（去除 import 区后）完全没有出现（词边界）时才删除该行。
带 `*` 通配与 `as` 别名的 import 一律跳过。

用法:
    python scripts/clean-unused-imports.py --src <目录>            # dry-run
    python scripts/clean-unused-imports.py --src <目录> --apply    # 写回
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True)
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    src = Path(args.src).resolve()

    files_changed = 0
    removed = 0

    for path in sorted(src.rglob("*.kt")):
        text = path.read_text(encoding="utf-8")
        lines = text.split("\n")
        body = "\n".join(l for l in lines if not l.strip().startswith("import "))
        out: list[str] = []
        changed = False
        for line in lines:
            s = line.strip()
            m = re.match(r"import ([\w.]+)$", s)
            if m:
                symbol = m.group(1).split(".")[-1]
                if symbol == "*":
                    out.append(line)
                    continue
                if not re.search(rf"\b{re.escape(symbol)}\b", body):
                    removed += 1
                    changed = True
                    continue
            out.append(line)
        if changed:
            files_changed += 1
            if args.apply:
                path.write_text("\n".join(out), encoding="utf-8")

    mode = "APPLIED" if args.apply else "DRY-RUN"
    print(f"[{mode}] files: {files_changed}; imports removed: {removed}")


if __name__ == "__main__":
    main()
