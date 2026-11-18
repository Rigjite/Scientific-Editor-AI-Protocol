#!/usr/bin/env python3
"""
mse_grammar.py — mechanical language slips for the scientific-editor skill
(language check, section 1e of SKILL.md). Python standard library only.

Finds slips a script can see without a dictionary or a parser, in Russian,
English and Japanese lines of the body text (the reference list is skipped):
  all       — a word written twice in a row («в в», "the the"); doubled spaces;
              a space before a comma or a full stop; no space after a comma or
              a semicolon between two words;
  Russian   — compound adjectives split by a space («сельско хозяйственный»,
              «научно исследовательский»): one word or a hyphen;
  Japanese  — mixed styles in one text (です・ます and だ・である, 公用文作成の
              考え方 Ⅲ-1イ); mixed punctuation (「、」 with 「，」, 「。」 with 「．」,
              Ⅰ-5(1)ア); full- and half-width digits or Latin letters mixed
              (Ⅰ-4エ, Ⅰ-6エ);
              doubled particles (「をを」, 「がが」); ら-less potential forms
              (「見れる」 for 「見られる」); wordy forms («することができる», «を実施した»,
              «ということになる», Ⅱ-5ウ(イ)); double negatives (Ⅲ-3コ); sentences
              longer than 100 characters (the guide asks to watch readability
              from 50–60, Ⅲ-3ア).

Agreement, government, commas and word choice need a reader: this tool is a
safety net for the language check, never a substitute for it. A finding is a
prompt to look; the journal's own rules win (some ask for 「，」 and 「．」).

Usage:
  python3 mse_grammar.py manuscript.docx|.md|.txt [--json]
Exit 0 = clean, 1 = findings, 2 = file could not be read.
"""
import json
import re
import sys
import zipfile
from xml.etree import ElementTree
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from mse_lint import is_japanese, is_russian, read_text, split_references  # noqa: E402

REPEAT = re.compile(r"\b([^\W\d_]{1,})\s+\1\b(?!-)", re.IGNORECASE)  # not «что что-то»
REPEAT_OK = {"had", "that", "ha", "no", "bye", "so", "very", "bla", "ну"}  # "had had", "that that" can be right
DOUBLE_SPACE = re.compile(r"\S {2,}\S")
SPACE_BEFORE = re.compile(r"[^\W\d_] +[,.;:](?![.\d])")
NO_SPACE_AFTER = re.compile(r"[^\W\d_]{2,}[,;][^\W\d_]{2,}")
SPLIT_FIRST = (r"сельско|научно|эколого|социально|технико|медико|физико|химико|историко|военно|финансово|"
               r"народно|культурно|учебно|опытно|проектно|строительно|информационно|производственно")
SPLIT_SECOND = (r"хозяйствен|исследовательск|экономическ|техническ|биологическ|химическ|математическ|"
                r"культурн|промышленн|конструкторск|методическ|аналитическ|коммуникационн|педагогическ")
SPLIT_COMPOUND = re.compile(rf"\b(?:{SPLIT_FIRST})\s+(?:{SPLIT_SECOND})\w*", re.IGNORECASE)

JA_SENT = re.compile(r"[^。．！？!?]+[。．！？!?]")
JA_POLITE = re.compile(r"(です|ます|でした|ました|ません|でしょう|ましょう)[。．]$")
JA_PLAIN = re.compile(r"(である|であった|であろう|だ|だった|ではない|た|る|ない|う)[。．]$")
JA_FULL_DIGITS = re.compile(r"[０-９]+")
JA_FULL_LATIN = re.compile(r"[Ａ-Ｚａ-ｚ]+")
JA_DOUBLE_PARTICLE = re.compile(r"(をを|がが|にに|でで|へへ|(?<!も)のの(?!し))")
RA_NUKI_STEMS = (r"見|来|出|寝|着|居|似|煮|起き|食べ|考え|答え|教え|忘れ|調べ|比べ|信じ|生き|借り|降り|浴び|"
                 r"伸び|延び|閉じ|感じ|決め|止め|始め|続け|受け|分け|避け|集め|求め|認め|確かめ|見つけ|得")
JA_RA_NUKI = re.compile(rf"(?:{RA_NUKI_STEMS})れ(?:る|ない|ます|ません|た|て|ず)")
JA_WORDY = re.compile(r"(することができ\w?|を実施し\w?|ということになる)")
JA_DOUBLE_NEG = re.compile(r"(ないわけではない|なくはない|ないことはない|ないとは言えない|ないとはいえない)")
JA_LONG = 100


def body_lines(lines):
    ref_at = split_references(lines)
    body = lines if ref_at is None else lines[:ref_at]
    return [l for l in body if l.strip() and not re.match(r"^\W*(УДК|UDC)\b", l.strip())]


def strip_quotes(text):
    """Quotations and bracketed text are not the author's style (公用文 Ⅲ-1イ)."""
    return re.sub(r"「[^」]*」|『[^』]*』|（[^）]*）|\([^)]*\)", "", text)


def check(lines):
    findings = []
    body = body_lines(lines)
    ja_lines = [l for l in body if is_japanese(l)]
    other = [l for l in body if not is_japanese(l)]

    for n, line in enumerate(body, 1):
        for m in REPEAT.finditer(line):
            if m.group(1).lower() not in REPEAT_OK and not m.group(1).isupper():
                findings.append(("repeat", n, f"«{m.group(0)}» — word written twice"))
        if DOUBLE_SPACE.search(line.strip()):
            findings.append(("space", n, "two or more spaces in a row"))
    for line in other:
        n = body.index(line) + 1
        for m in SPACE_BEFORE.finditer(line):
            findings.append(("space", n, f"«{m.group(0).strip()}» — space before a punctuation mark"))
        for m in NO_SPACE_AFTER.finditer(line):
            findings.append(("space", n, f"«{m.group(0)}» — no space after the comma or semicolon"))
        if is_russian(line):
            for m in SPLIT_COMPOUND.finditer(line):
                findings.append(("compound", n, f"«{m.group(0)}» — one word or a hyphen (check the dictionary)"))

    if ja_lines:
        text = "\n".join(ja_lines)
        sents = [s.strip() for s in JA_SENT.findall(strip_quotes(text).replace("\n", ""))]
        polite = [s for s in sents if JA_POLITE.search(s)]
        plain = [s for s in sents if not JA_POLITE.search(s) and JA_PLAIN.search(s)]
        if polite and plain:
            minority = polite if len(polite) <= len(plain) else plain
            kind = "です・ます" if minority is polite else "だ・である"
            findings.append(("style", None, f"styles mixed: {len(polite)} です・ます and {len(plain)} だ・である sentences; "
                                            f"the {kind} ones, e.g. «{minority[0][:40]}…» — keep one style"))
        commas = len(re.findall(r"(?<![\d０-９])，", text))  # not «1，000»
        stops = len(re.findall(r"(?<![\d０-９])．", text))  # not section numbers «2．方法»
        if "、" in text and commas:
            findings.append(("punct", None, f"both 「、」 ({text.count('、')}) and 「，」 ({commas}) — use one"))
        if "。" in text and stops:
            findings.append(("punct", None, f"both 「。」 ({text.count('。')}) and 「．」 ({stops}) — use one"))
        for pattern, half, name in ((JA_FULL_DIGITS, r"[0-9]", "digits"), (JA_FULL_LATIN, r"[A-Za-z]", "Latin letters")):
            full = pattern.findall(text)
            if full and re.search(half, text):  # one width throughout the document (Ⅰ-4エ, Ⅰ-6エ)
                findings.append(("width", None, f"full- and half-width {name} mixed, e.g. «{full[0]}» — use one width"))
        for line in ja_lines:
            n = body.index(line) + 1
            for m in JA_DOUBLE_PARTICLE.finditer(line):
                findings.append(("particle", n, f"«{m.group(0)}» — doubled particle"))
            for m in JA_RA_NUKI.finditer(line):
                findings.append(("ra-nuki", n, f"«{m.group(0)}» — ら-less potential form; use the standard form (見られる, 来られる)"))
            for m in JA_DOUBLE_NEG.finditer(line):
                findings.append(("negation", n, f"«{m.group(0)}» — double negative; say it directly"))
        wordy = JA_WORDY.findall(text)
        if wordy:
            counts = {}
            for w in wordy:
                counts[w] = counts.get(w, 0) + 1
            findings.append(("wordy", None, "wordy forms: " + ", ".join(f"«{k}» ×{v}" for k, v in counts.items())
                                            + " — «できる», «調査した» instead"))
        for s in sents:
            if len(re.sub(r"\s", "", s)) > JA_LONG:
                findings.append(("long", None, f"{len(s)} characters: «{s[:30]}…» — split it"))
    return findings


def main(argv):
    args = [a for a in argv[1:] if not a.startswith("--")]
    if len(args) != 1:
        print("usage: python3 mse_grammar.py manuscript.docx|.md|.txt [--json]")
        return 2
    try:
        lines = read_text(args[0])
    except (OSError, KeyError, zipfile.BadZipFile, ElementTree.ParseError) as exc:
        print(f"cannot read input: {exc}")
        return 2
    found = check(lines)
    if "--json" in argv:
        print(json.dumps([{"check": c, "line": n, "message": m} for c, n, m in found], ensure_ascii=False, indent=2))
    elif not found:
        print("clean — no mechanical slips found (agreement, commas and word choice still need a reader)")
    else:
        print(f"{len(found)} finding(s):")
        for check_name, n, msg in found:
            print(f" - [{check_name}]" + (f" line {n}:" if n else "") + f" {msg}")
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
