#!/usr/bin/env python3
"""
mse_lint.py — formatting linter for the scientific-editor skill (Appendix T).

Reads .md / .txt / .docx (Python standard library only) and checks:
  1. Citations: [N] markers in order of first use, no gaps (1, 2, 3 …).
  2. Reference list: every cited number has an entry and every entry is cited.
     Recognizes GOST-style lists ("1. Author …") and bracketed lists ("[1] …")
     under a heading such as «Список источников», «Список литературы»,
     «Литература», «Библиографический список» or «References».
  3. Russian decimal comma: flags 3.14 in Russian-language lines.
  4. Number–unit spacing: flags digits glued to a Cyrillic word or unit (5мг, 220°C).
  5. Quotation marks: flags straight "…" quotes in Russian-language lines.

To avoid false alarms it skips: the reference list (for checks 3–5), lines in
English or other Latin-script languages, the УДК/UDC line, dates (22.10.2026),
version numbers (v2.2, версия 2.2), DOIs, URLs and e-mail addresses.

Usage:
  python3 mse_lint.py manuscript.docx|.md|.txt [--json]
Exit 0 = clean, 1 = findings, 2 = file could not be read.
Scope: formatting only — a clean run never substitutes for Gates A–D.
"""
import json
import re
import sys
import zipfile
from xml.etree import ElementTree

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"

REF_HEADING = re.compile(
    r"^\W*(список\s+(использованных\s+)?(источников|литературы)|литература|"
    r"библиографический\s+список|references|bibliography)\W*$",
    re.IGNORECASE,
)
CITE_BLOCK = re.compile(r"\[([^\[\]]{1,80})\]")
REF_ENTRY = re.compile(r"^\s*(?:\[(\d{1,3})\]|(\d{1,3})[.)])\s+\S")
DECIMAL = re.compile(r"(?<![\w.,/:\-])(\d+)\.(\d+)(?![\w./])")
GLUED = re.compile(r"\d(?:°\s?[CС]|[а-яё])", re.IGNORECASE)
VERSION_WORDS = ("версия", "версии", "версию", "version", "ver", "v", "rev")
SKIP_TOKEN = re.compile(r"(https?://|www\.|doi[:.]|10\.\d{4,}/|@)", re.IGNORECASE)


def read_text(path):
    """Return the document as a list of lines (one paragraph per line for .docx)."""
    if path.lower().endswith(".docx"):
        with zipfile.ZipFile(path) as z:
            root = ElementTree.fromstring(z.read("word/document.xml"))
        lines = []
        for p in root.iter(W + "p"):
            parts = []
            for node in p.iter():
                if node.tag == W + "t" and node.text:
                    parts.append(node.text)
                elif node.tag == W + "tab":
                    parts.append("\t")
                elif node.tag in (W + "br", W + "cr"):
                    parts.append(" ")
            lines.append("".join(parts))
        return lines
    with open(path, encoding="utf-8") as f:
        text = f.read()
    # undo Markdown backslash escapes (pandoc writes \[1\] for [1])
    return re.sub(r"\\([\[\]_*#.()<>-])", r"\1", text).splitlines()


def is_russian(line):
    """True when most letters in the line are Cyrillic."""
    cyr = len(re.findall(r"[а-яё]", line, re.IGNORECASE))
    lat = len(re.findall(r"[a-z]", line, re.IGNORECASE))
    return cyr > 0 and cyr >= lat


def split_references(lines):
    """Index of the reference-list heading, or None."""
    for i, line in enumerate(lines):
        if REF_HEADING.match(line.strip().strip("#*_ ").strip()):
            return i
    return None


def cited_numbers(text):
    """Citation numbers in order of appearance; expands [3–5] and [1, 4; 7]."""
    out = []
    for block in CITE_BLOCK.findall(text):
        for token in re.split(r"[,;]", block):
            token = token.strip()
            rng = re.fullmatch(r"(\d{1,3})\s*[–—-]\s*(\d{1,3})", token)
            if rng:
                a, b = int(rng.group(1)), int(rng.group(2))
                if a < b <= a + 50:
                    out.extend(range(a, b + 1))
            elif re.fullmatch(r"\d{1,3}", token):
                out.append(int(token))
    return out


def _is_version(line, start):
    """Version or standard number: 'версия 2.2', 'v 2.2', 'CC BY 4.0', 'Python 3.9'."""
    before = line[:start].rstrip().split()
    if not before:
        return False
    word = before[-1].strip("(«\"")
    return word.lower() in VERSION_WORDS or bool(re.fullmatch(r"[A-Z][A-Za-z-]*", word))


def lint(lines):
    findings = []
    ref_at = split_references(lines)
    body = lines if ref_at is None else lines[:ref_at]
    refs = [] if ref_at is None else lines[ref_at + 1:]

    # 1. Citation order and gaps
    cites = cited_numbers("\n".join(body))
    first_use = []
    for c in cites:
        if c not in first_use:
            first_use.append(c)
    if first_use:
        if first_use != sorted(first_use):
            findings.append(("citations", None, f"order of first use is not sequential: {first_use}"))
        gaps = sorted(set(range(1, max(first_use) + 1)) - set(first_use))
        if gaps:
            findings.append(("citations", None, f"numbers never cited in the text: {gaps}"))

    # 2. Reference list coverage
    if first_use:
        if ref_at is None:
            findings.append(("references", None, "reference-list heading not found"))
        else:
            listed = []
            for line in refs:
                m = REF_ENTRY.match(line)
                if m:
                    listed.append(int(m.group(1) or m.group(2)))
            missing = [c for c in first_use if c not in listed]
            unused = [n for n in listed if n not in first_use]
            if missing:
                findings.append(("references", None, f"cited but no reference-list entry: {missing}"))
            if unused:
                findings.append(("references", None, f"listed but never cited: {unused}"))

    # 3–5. Russian typography (body only, Russian-language lines only)
    for i, line in enumerate(body, 1):
        stripped = line.strip()
        if not stripped or not is_russian(stripped):
            continue
        if re.match(r"^\W*(УДК|UDC)\b", stripped):
            continue
        no_html = re.sub(r"<[^>]+>", " ", line)  # inline HTML in Markdown exports
        clean = " ".join(t for t in no_html.split() if not SKIP_TOKEN.search(t))
        for m in DECIMAL.finditer(clean):
            if _is_version(clean, m.start()):
                continue
            findings.append(("decimal", i, f"decimal point '{m.group()}' — use a comma in Russian text"))
        for m in GLUED.finditer(clean):
            findings.append(("spacing", i, f"'{m.group()}' — put a (non-breaking) space between number and unit"))
        if '"' in clean:
            findings.append(("quotes", i, "straight quotes — use «…» in Russian text"))
    return findings


def main(argv):
    args = [a for a in argv[1:] if not a.startswith("--")]
    if len(args) != 1:
        print(__doc__.strip().splitlines()[0])
        print("usage: python3 mse_lint.py manuscript.docx|.md|.txt [--json]")
        return 2
    try:
        lines = read_text(args[0])
    except (OSError, KeyError, zipfile.BadZipFile, ElementTree.ParseError) as exc:
        print(f"cannot read {args[0]}: {exc}")
        return 2
    findings = lint(lines)
    text = "\n".join(lines)
    stats = {"chars_with_spaces": len(text), "chars_without_spaces": len(re.sub(r"\s", "", text))}
    if "--json" in argv:
        print(json.dumps({"findings": [{"check": c, "line": n, "message": m} for c, n, m in findings],
                          "stats": stats, "result": "findings" if findings else "clean"},
                         ensure_ascii=False, indent=2))
    else:
        if findings:
            print(f"{len(findings)} finding(s):")
            for check, line_no, msg in findings:
                where = f"L{line_no}: " if line_no else ""
                print(f" - [{check}] {where}{msg}")
        else:
            print("clean")
        print(f"length: {stats['chars_with_spaces']} characters with spaces, "
              f"{stats['chars_without_spaces']} without")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
