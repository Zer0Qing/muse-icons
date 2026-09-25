#!/usr/bin/env python3
"""恢复被 clean-unused-imports 误删的 Compose delegate import（getValue / setValue）。

这些 import 是 `by` 委托语法隐式使用的，文本中不出现符号名，必须保留。
从 `git diff` 中找出被删除的这些 import 行，为对应文件补回（正文含 "by " 时）。
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

REPO = Path("E:/1Project/Muse/1muse")
TARGET_RE = re.compile(r"^-import androidx\.compose\.runtime\.(getValue|setValue)$")


def main() -> None:
    diff = subprocess.run(
        ["git", "diff", "HEAD", "--", "app/src/main/java"],
        cwd=REPO,
        capture_output=True,
        text=True,
        encoding="utf-8",
    ).stdout

    cur: str | None = None
    targets: dict[str, set[str]] = {}
    for line in diff.split("\n"):
        m = re.match(r"^diff --git a/(.+?) b/", line)
        if m:
            cur = m.group(1)
        if cur and TARGET_RE.match(line.strip()):
            targets.setdefault(cur, set()).add(line.strip()[1:])

    restored = 0
    for rel, imps in sorted(targets.items()):
        path = REPO / rel
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        if "by " not in text:
            continue
        lines = text.split("\n")
        for imp in sorted(imps):
            if imp in text:
                continue
            insert_at = None
            last_import = None
            for i, l in enumerate(lines):
                if l.startswith("import "):
                    last_import = i
                    if l > imp:
                        insert_at = i
                        break
            if insert_at is None:
                insert_at = (last_import + 1) if last_import is not None else 0
            lines.insert(insert_at, imp)
            restored += 1
        path.write_text("\n".join(lines), encoding="utf-8")

    print(f"restored {restored} import(s) across {len(targets)} file(s)")


if __name__ == "__main__":
    main()
