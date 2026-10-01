#!/usr/bin/env python3
"""
Hygiene check: Fails if 'localhost', '127.0.0.1', or ':8000' appears in frontend/src/
Cross-platform stdlib runner.
"""
import sys
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TARGET_DIR = REPO_ROOT / "frontend" / "src"

FORBIDDEN_PATTERN = re.compile(r"(localhost|127\.0\.0\.1|:8000)")

def main():
    if not TARGET_DIR.exists():
        print(f"Error: Target directory {TARGET_DIR} does not exist", file=sys.stderr)
        sys.exit(1)

    violations = []
    for file_path in TARGET_DIR.rglob("*"):
        if file_path.is_file() and file_path.suffix in (".ts", ".tsx", ".js", ".jsx", ".html", ".css"):
            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
                for line_no, line in enumerate(content.splitlines(), start=1):
                    if FORBIDDEN_PATTERN.search(line):
                        rel_path = file_path.relative_to(REPO_ROOT)
                        violations.append((rel_path, line_no, line.strip()))
            except Exception as e:
                print(f"Warning reading {file_path}: {e}", file=sys.stderr)

    if violations:
        print("ERROR: Hardcoded host violations detected in frontend/src/:", file=sys.stderr)
        for path, line_no, text in violations:
            print(f"  {path}:{line_no} -> {text}", file=sys.stderr)
        print("All frontend API and WebSocket URLs must use src/lib/config.ts.", file=sys.stderr)
        sys.exit(1)

    print("PASSED: Zero hardcoded host violations found in frontend/src/.")
    sys.exit(0)

if __name__ == "__main__":
    main()
