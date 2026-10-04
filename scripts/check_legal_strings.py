#!/usr/bin/env python3
"""
Grep Guard: Check for hardcoded legal provisions outside single source of truth.
Fails on matches of IPC, CrPC, Evidence Act, BNS, BNSS, BSA, 65B, 420, 66D, or section patterns.
"""
import os
import re
import sys
from pathlib import Path

FORBIDDEN_PATTERNS = [
    (re.compile(r"\bIPC\b"), "IPC"),
    (re.compile(r"\bCrPC\b"), "CrPC"),
    (re.compile(r"\bEvidence Act\b"), "Evidence Act"),
    (re.compile(r"\bBNS\b"), "BNS"),
    (re.compile(r"\bBNSS\b"), "BNSS"),
    (re.compile(r"\bBSA\b"), "BSA"),
    (re.compile(r"\b65B\b"), "65B"),
    (re.compile(r"\b420\b"), "420"),
    (re.compile(r"\b66D\b"), "66D"),
    (re.compile(r"\b(s\.|sec\.|section|U/S)\s*\d+", re.IGNORECASE), "Section Pattern"),
]

EXEMPT_DIRS = [
    Path("backend/app/legal"),
    Path("app/legal"),
    Path("docs/research"),
    Path("tests/fixtures"),
    Path("backend/tests/fixtures"),
]

EXEMPT_FILES = [
    Path("app/legal/provisions.yaml"),
    Path("backend/app/legal/provisions.yaml"),
    Path("docs/LEGAL_NOTES.md"),
    Path("backend/docs/LEGAL_NOTES.md"),
    Path("scripts/check_legal_strings.py"),
    Path("scripts/legal_strings_allowlist.txt"),
]

TARGET_DIRS = [
    Path("backend/app"),
    Path("frontend/src"),
]

def load_allowlist(allowlist_file: Path):
    allowlist = []
    if not allowlist_file.exists():
        return allowlist
    with open(allowlist_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split(":", 2)
            if len(parts) >= 2:
                allowlist.append((parts[0].replace("\\", "/"), parts[1]))
    return allowlist

def is_exempt(path: Path) -> bool:
    norm = str(path).replace("\\", "/")
    for ef in EXEMPT_FILES:
        if str(ef).replace("\\", "/") in norm:
            return True
    for ed in EXEMPT_DIRS:
        if str(ed).replace("\\", "/") in norm:
            return True
    return False


def check_file(file_path: Path, allowlist: list):
    violations = []
    rel_path = str(file_path).replace("\\", "/")
    
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            for line_no, line in enumerate(f, 1):
                # Check allowlist
                is_allowed = False
                for a_file, a_pat in allowlist:
                    if a_file in rel_path:
                        if a_pat.isdigit() and int(a_pat) == line_no:
                            is_allowed = True
                            break
                        elif a_pat in line:
                            is_allowed = True
                            break
                if is_allowed:
                    continue

                for pattern, name in FORBIDDEN_PATTERNS:
                    match = pattern.search(line)
                    if match:
                        violations.append((rel_path, line_no, name, line.strip()))
    except Exception as e:
        print(f"Error reading {file_path}: {e}", file=sys.stderr)
    return violations

def main():
    root = Path(__file__).resolve().parent.parent
    allowlist_file = root / "scripts" / "legal_strings_allowlist.txt"
    allowlist = load_allowlist(allowlist_file)

    all_violations = []
    for td in TARGET_DIRS:
        dir_path = root / td
        if not dir_path.exists():
            continue
        for root_dir, _, files in os.walk(dir_path):
            for file in files:
                ext = Path(file).suffix.lower()
                if ext not in [".py", ".ts", ".tsx", ".js", ".jsx", ".html", ".jinja", ".jinja2"]:
                    continue
                file_path = Path(root_dir) / file
                rel_path = file_path.relative_to(root)
                if is_exempt(rel_path):
                    continue
                v = check_file(file_path, allowlist)
                all_violations.extend(v)

    if all_violations:
        print(f"FAILED: Found {len(all_violations)} hardcoded legal string violation(s):", file=sys.stderr)
        for rel_path, line_no, name, content in all_violations:
            print(f"  {rel_path}:{line_no}: [{name}] {content}", file=sys.stderr)
        sys.exit(1)
    else:
        print("PASSED: Zero hardcoded legal string violations detected outside single source of truth.")
        sys.exit(0)

if __name__ == "__main__":
    main()
