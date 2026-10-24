#!/usr/bin/env python3
"""
mse_diff.py — compare two versions of a manuscript for the review-edits mode
of the scientific-editor skill (Python standard library only).

Reads .md / .txt / .docx. Lists every changed sentence and flags what an
editor must not let through unchecked:
  * NEW NUMBER   — a number in the edited version that the base version never had
                   (it needs a source before it can be accepted);
  * NEW CITATION — a [N] marker the base version never had;
  * FORBIDDEN    — a term the author excluded (--forbid "term1,term2"),
                   reported wherever it occurs in the edited version;
  * MISSING NUMBER — a number the base version had and the edited one lost
                   (a style edit must not drop a fact; in review-edits it shows deletions).
It also reports the change in length, which matters for page limits.

Usage:
  python3 mse_diff.py base.docx edited.docx [--forbid "term1,term2"] [--json]
Exit 0 = no flags, 1 = flags found (new or missing numbers, new citations, forbidden terms),
2 = a file could not be read.
The tool only lists changes; accepting or rejecting each one is the editor's call.
"""
import difflib
import json
import os
import re
import sys
import zipfile
from xml.etree import ElementTree

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mse_lint import cited_numbers, read_text  # noqa: E402

NUMBER = re.compile(r"(?<![\w])\d+(?:[.,]\d+)?")
SENT_END = re.compile(r"(?<=[.!?…])\s+(?=[«\"(\[]?[A-ZА-ЯЁ0-9])")
ABBREV = {"оз", "г", "гг", "т", "с", "ст", "др", "им", "рис", "табл", "см", "ср", "напр", "пр", "р",
          "м.-б.м", "et al", "al", "e.g", "i.e", "vol", "no", "p", "pp", "art", "fig", "eq", "dr", "prof"}


def sentences(lines):
    """Split paragraphs into sentences; keep table rows and headings whole."""
    out = []
    for line in lines:
        line = " ".join(line.split())
        if not line:
            continue
        if line.startswith("|") or len(line) < 60:
            out.append(line)
            continue
        start = 0
        for m in SENT_END.finditer(line):
            last = line[start:m.start()].split()[-1].rstrip(".").lower() if line[start:m.start()].split() else ""
            if last in ABBREV or re.fullmatch(r"[^\W\d_](?:\.-?[^\W\d_])*", last):  # «оз. Бейра», «Р.М. Иванова»
                continue
            out.append(line[start:m.start()])
            start = m.end()
        out.append(line[start:])
    return [s for s in out if s.strip()]


def numbers(text):
    """Normalized numbers: decimal comma → point, leading zeros dropped."""
    found = set()
    text = re.sub(r"\[[\d\s,;–—-]+\]", " ", text)  # citation markers are reported separately
    for m in NUMBER.finditer(text):
        whole, _, frac = m.group().replace(",", ".").partition(".")
        frac = frac.rstrip("0")
        found.add(str(int(whole)) + ("." + frac if frac else ""))
    return found


def diff(base_lines, new_lines, forbid=()):
    base_s, new_s = sentences(base_lines), sentences(new_lines)
    base_text, new_text = "\n".join(base_lines), "\n".join(new_lines)
    base_nums = numbers(base_text)
    base_cites = set(cited_numbers(base_text))
    changes = []
    matcher = difflib.SequenceMatcher(a=base_s, b=new_s, autojunk=False)
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            continue
        old, new = " ".join(base_s[i1:i2]), " ".join(new_s[j1:j2])
        kind = {"replace": "changed", "delete": "removed", "insert": "added"}[tag]
        new_numbers = sorted(numbers(new) - base_nums, key=lambda x: (len(x), x)) if new else []
        new_cites = sorted(set(cited_numbers(new)) - base_cites) if new else []
        changes.append({"kind": kind, "before": old, "after": new,
                        "new_numbers": new_numbers, "new_citations": new_cites})
    forbidden = []
    for term in forbid:
        hits = [s for s in new_s if term.lower() in s.lower()]
        if hits:
            forbidden.append({"term": term, "count": len(hits), "example": hits[0][:160]})
    words_base, words_new = len(base_text.split()), len(new_text.split())
    stats = {"words_base": words_base, "words_edited": words_new,
             "change_percent": round(100.0 * (words_new - words_base) / max(words_base, 1), 1),
             "missing_numbers": sorted(base_nums - numbers(new_text), key=lambda x: (len(x), x))}
    return changes, forbidden, stats


def _short(text, limit=140):
    return text if len(text) <= limit else text[: limit - 1] + "…"


def main(argv):
    args, forbid = [], []
    it = iter(argv[1:])
    for a in it:
        if a == "--forbid":
            forbid = [t.strip() for t in next(it, "").split(",") if t.strip()]
        elif not a.startswith("--"):
            args.append(a)
    if len(args) != 2:
        print("usage: python3 mse_diff.py base edited [--forbid \"term1,term2\"] [--json]")
        return 2
    try:
        base, new = read_text(args[0]), read_text(args[1])
    except (OSError, KeyError, zipfile.BadZipFile, ElementTree.ParseError) as exc:
        print(f"cannot read input: {exc}")
        return 2
    changes, forbidden, stats = diff(base, new, forbid)
    flagged = (any(c["new_numbers"] or c["new_citations"] for c in changes) or bool(forbidden)
               or bool(stats["missing_numbers"]))
    if "--json" in argv:
        print(json.dumps({"changes": changes, "forbidden": forbidden, "stats": stats,
                          "result": "flags" if flagged else "no flags"}, ensure_ascii=False, indent=2))
        return 1 if flagged else 0
    print(f"{len(changes)} change(s); length {stats['words_base']} → {stats['words_edited']} words "
          f"({stats['change_percent']:+} %)")
    if stats["missing_numbers"]:
        print("MISSING NUMBER (in base, not in edited): " + ", ".join(stats["missing_numbers"]))
    for term in forbidden:
        print(f"FORBIDDEN '{term['term']}' ×{term['count']}: {_short(term['example'])}")
    print("\n| # | Type | Before | After | Flags | Decision |\n|---|---|---|---|---|---|")
    for n, c in enumerate(changes, 1):
        flags = []
        if c["new_numbers"]:
            flags.append("NEW NUMBER: " + ", ".join(c["new_numbers"]))
        if c["new_citations"]:
            flags.append("NEW CITATION: " + ", ".join(map(str, c["new_citations"])))
        cells = [str(n), c["kind"], _short(c["before"]).replace("|", "/"),
                 _short(c["after"]).replace("|", "/"), "; ".join(flags) or "—", ""]
        print("| " + " | ".join(cells) + " |")
    return 1 if flagged else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
