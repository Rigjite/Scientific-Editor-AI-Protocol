#!/usr/bin/env python3
"""
mse_lint.py — companion linter for my-scientific-editor (Appendix T).
Checks a manuscript (plain text / Markdown) for:
  1. Citation order: [N] markers must appear in sequential order of first use.
  2. Russian decimal commas: flags digit.digit patterns (likely should be comma).
  3. Number-unit spacing: flags digits glued to letters (5mg) — needs space.
  4. Russian quotes: flags straight "..." quotes (should be «...»).
  5. Reference list: every [N] cited must have a matching list entry.

Usage: python3 mse_lint.py manuscript.md
Exit 0 = clean, 1 = findings.
Scope: formatting only — a clean run never substitutes for Gates A-D.
"""
import re
import sys

def main(path):
    text = open(path, encoding="utf-8").read()
    findings = []

    # 1. Citation order
    cites = [int(m) for m in re.findall(r"\[(\d+)\]", text)]
    seen, order = set(), []
    for c in cites:
        if c not in seen:
            seen.add(c)
            order.append(c)
    if order != sorted(order):
        findings.append(f"citations out of order: first-use sequence {order}")

    # 5. Reference list coverage (heuristic: lines starting with [N])
    ref_entries = set(int(m) for m in re.findall(r"^\[(\d+)\]", text, re.M))
    missing = [c for c in order if c not in ref_entries]
    if missing and ref_entries:
        findings.append(f"cited but no reference-list entry: {missing}")

    for i, line in enumerate(text.splitlines(), 1):
        # 2. Decimal points in Russian text
        for m in re.finditer(r"\d+\.\d+", line):
            findings.append(f"L{i}: possible decimal point '{m.group()}' — use comma in RU text")
        # 3. Digit glued to letter
        for m in re.finditer(r"\d[а-яА-Яa-zA-Z]", line):
            if not re.match(r"\d\.", m.group()):  # skip list numbering like "1."
                findings.append(f"L{i}: missing space between number and unit '{m.group()}'")
        # 4. Straight quotes
        if '"' in line:
            findings.append(f"L{i}: straight quotes — use « » in RU text")

    if findings:
        print(f"{len(findings)} finding(s):")
        for f in findings:
            print(" -", f)
        return 1
    print("clean")
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
