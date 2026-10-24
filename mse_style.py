#!/usr/bin/env python3
"""
mse_style.py — style and voice diagnostics for the scientific-editor skill
(voice pass, section 1c of SKILL.md). Python standard library only.

Measures the markers that make academic prose read as machine-made, in
Russian or English, and points to the exact sentences:
  * author voice      — authorial "мы / наш" or "we / our" in the body;
  * sentence rhythm   — mean length, variation (CV), share of very long sentences;
  * glued clauses     — semicolons, spaced dashes and parentheses per 1000 words;
  * noun chains       — nominalization density (канцелярит, "zombie nouns");
  * stock phrases     — Russian bureaucratic clichés and English words that
                        LLM-edited abstracts overuse (Kobak et al. 2025);
  * self-repetition   — five-word phrases shared by the abstract and the conclusions;
  * repeated openers  — the same first word at the start of many sentences.
With --reference FILE (one or more texts whose style the author wants to
match, e.g. the author's own papers written without AI) the same metrics are
computed for the reference and shown side by side.

Thresholds are editorial heuristics for classic academic prose, not norms:
a flag is a prompt to look, never proof that a text was machine-written.
This tool does not detect AI and must not be used to hide AI use — the
manuscript discloses AI assistance in any case (Gate C).

Usage:
  python3 mse_style.py manuscript.docx [--reference my_2003_paper.docx ...] [--json]
Exit 0 = no flags, 1 = flags, 2 = a file could not be read.
"""
import json
import os
import re
import statistics
import sys
import zipfile
from xml.etree import ElementTree

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mse_diff import sentences  # noqa: E402
from mse_lint import is_russian, read_text, split_references  # noqa: E402

LIMITS = {  # (ru, en)
    "long_sentence_words": (40, 35),
    "long_sentence_share": (0.15, 0.15),
    "min_cv": (0.35, 0.35),
    "semicolons_per_1000": (8.0, 8.0),
    "dashes_per_1000": (15.0, 12.0),
    "parentheses_per_1000": (15.0, 15.0),
    "nominalizations_per_100": (7.0, 6.0),
    "shared_5grams_abstract_conclusions": (5, 5),
    "same_opener": (4, 4),
}
VOICE = {"ru": r"\b(мы|нами|нас|нам|наш\w*)\b", "en": r"\b(we|our|ours|us)\b"}
NOMINAL = {
    "ru": r"\b\w{4,}(?:ние|ния|нию|нием|нии|ниям|ниями|ниях|ция|ции|цию|цией|ость|ости|остью)\b",
    "en": r"\b\w{3,}(?:tion|tions|ment|ments|ness|ity|ities|ance|ence)\b",
}
STOCK = {
    "ru": [r"\bявля(?:ется|ются|ющ\w*)\b", r"\bданн(?:ый|ая|ое|ого|ой|ом|ую)\b",
           r"\bосуществля\w*", r"\bв рамках\b", r"\bигра\w+ (?:важную|ключевую|значительную) роль\b",
           r"\b(?:важно|следует|необходимо|стоит) отметить\b", r"\bтаким образом\b",
           r"\bв свою очередь\b", r"\bна сегодняшний день\b", r"\bпредставляет собой\b",
           r"\bпозволяет (?:обеспечить|осуществить|повысить|снизить)\b",
           r"\bобеспечива\w+ (?:возможность|снижение|повышение)\b", r"\bуникальн\w+", r"\bинновационн\w+"],
    "en": [r"\bdelv(?:e|es|ed|ing)\b", r"\bunderscor(?:e|es|ed|ing)\b", r"\bshowcas(?:e|es|ed|ing)\b",
           r"\bcrucial\b", r"\bpivotal\b", r"\bintricate\b", r"\bnotably\b", r"\bcomprehensive\b",
           r"\badditionally\b", r"\binsights?\b", r"\bit is (?:important|worth) (?:to note|noting)\b",
           r"\bplays? a (?:crucial|key|pivotal|vital) role\b", r"\bin the realm of\b", r"\ba testament to\b"],
}
ABSTRACT = re.compile(r"^\W*(аннотация|резюме|abstract|summary)\b", re.I)
KEYWORDS = re.compile(r"^\W*(ключевые слова|keywords?)\b", re.I)
CAPTION = re.compile(r"^\W*(рисунок|рис\.|таблица|figure|fig\.|table)\s*\d", re.I)
BACK_MATTER = re.compile(r"^\W*(конфликт интересов|благодарност|финансирование|acknowledg|funding|conflicts? of interest|competing interests|author contributions)", re.I)
CONCLUSIONS = re.compile(r"^\W*(выводы|заключение|conclusions?|concluding remarks)\W*$", re.I)


def detect_language(paragraphs):
    ru = sum(1 for p in paragraphs if is_russian(p))
    return "ru" if ru >= len(paragraphs) / 2 else "en"


def sections(lines):
    """Split lines into abstract, body and conclusions (all before the reference list)."""
    ref_at = split_references(lines)
    lines = lines if ref_at is None else lines[:ref_at]
    abstract, conclusions, body = [], [], []
    mode = "body"
    for line in lines:
        stripped = line.strip()
        if ABSTRACT.match(stripped):
            mode = "abstract"
        elif KEYWORDS.match(stripped):
            mode = "body"
            continue
        elif CONCLUSIONS.match(stripped):
            mode = "conclusions"
            continue
        elif BACK_MATTER.match(stripped):
            mode = "back"
        if mode == "back" or CAPTION.match(stripped):
            continue
        {"abstract": abstract, "body": body, "conclusions": conclusions}[mode].append(line)
    return abstract, body, conclusions


def five_grams(text):
    words = re.findall(r"[^\W\d_]+", text.lower())
    return {" ".join(words[i:i + 5]) for i in range(len(words) - 4)}


def profile(lines, lang=None):
    """Style metrics for one document (main-language prose paragraphs only)."""
    abstract, body, conclusions = sections(lines)
    prose = [p for p in body + conclusions if len(p.split()) >= 12]
    if not prose:
        return None
    lang = lang or detect_language(prose)
    prose = [p for p in prose if is_russian(p) == (lang == "ru")]
    text = " ".join(prose)
    sents = [s for s in sentences(prose) if len(s.split()) >= 3]
    lengths = [len(s.split()) for s in sents]
    words = len(re.findall(r"[^\W\d_]+", text))
    if not words or not lengths:
        return None
    i = 0 if lang == "ru" else 1
    long_limit = LIMITS["long_sentence_words"][i]
    nominal_hits = re.findall(NOMINAL[lang], text, re.I)
    stock_hits = []
    for pattern in STOCK[lang]:
        stock_hits += [m.group(0) for m in re.finditer(pattern, text, re.I)]
    openers = {}
    for s in sents:
        first = re.sub(r"\W", "", s.split()[0].lower())
        if first:
            openers[first] = openers.get(first, 0) + 1
    abstract_text = " ".join(abstract)
    shared = sorted(five_grams(abstract_text) & five_grams(" ".join(conclusions))) if abstract and conclusions else []
    mean = statistics.mean(lengths)
    return {
        "language": lang,
        "words": words,
        "sentences": len(sents),
        "mean_sentence_words": round(mean, 1),
        "cv_sentence_length": round(statistics.pstdev(lengths) / mean, 2),
        "long_sentence_share": round(sum(n > long_limit for n in lengths) / len(lengths), 2),
        "long_sentences": [s for s in sents if len(s.split()) > long_limit],
        "author_voice": len(re.findall(VOICE[lang], text, re.I)),
        "semicolons_per_1000": round(1000 * text.count(";") / words, 1),
        "dashes_per_1000": round(1000 * len(re.findall(r"\s[–—]\s", text)) / words, 1),
        "parentheses_per_1000": round(1000 * text.count("(") / words, 1),
        "nominalizations_per_100": round(100 * len(nominal_hits) / words, 1),
        "stock_phrases": stock_hits,
        "shared_5grams_abstract_conclusions": shared,
        "top_openers": sorted(openers.items(), key=lambda kv: -kv[1])[:3],
    }


def flags(p):
    i = 0 if p["language"] == "ru" else 1
    out = []
    if p["author_voice"] == 0 and p["words"] >= 400:
        out.append(("voice", "no authorial 'мы/наш' ('we/our') in the body: the text has no author"))
    if p["long_sentence_share"] > LIMITS["long_sentence_share"][i]:
        out.append(("rhythm", f"{int(100 * p['long_sentence_share'])} % of sentences are longer than "
                              f"{LIMITS['long_sentence_words'][i]} words — split them"))
    if p["cv_sentence_length"] < LIMITS["min_cv"][i]:
        out.append(("rhythm", f"sentence lengths are monotonous (CV {p['cv_sentence_length']}) — mix short and long"))
    for key, name in (("semicolons_per_1000", "semicolons"), ("dashes_per_1000", "spaced dashes"),
                      ("parentheses_per_1000", "parentheses")):
        if p[key] > LIMITS[key][i]:
            out.append(("glue", f"{p[key]} {name} per 1000 words (above {LIMITS[key][i]}) — clauses are glued together"))
    if p["nominalizations_per_100"] > LIMITS["nominalizations_per_100"][i]:
        out.append(("nouns", f"{p['nominalizations_per_100']} nominalizations per 100 words — turn nouns back into verbs"))
    if p["stock_phrases"]:
        counts = {}
        for s in p["stock_phrases"]:
            counts[s.lower()] = counts.get(s.lower(), 0) + 1
        out.append(("stock", "stock phrases: " + ", ".join(f"«{k}» ×{v}" for k, v in counts.items())))
    if len(p["shared_5grams_abstract_conclusions"]) >= LIMITS["shared_5grams_abstract_conclusions"][i]:
        out.append(("repeat", f"{len(p['shared_5grams_abstract_conclusions'])} five-word phrases repeat between "
                              "the abstract and the conclusions — conclusions should answer 'so what?', not restate"))
    for word, n in p["top_openers"]:
        if n >= LIMITS["same_opener"][i]:
            out.append(("openers", f"{n} sentences start with «{word}»"))
    return out


def _short(s, n=110):
    return s if len(s) <= n else s[: n - 1] + "…"


def main(argv):
    args, refs, as_json = [], [], "--json" in argv
    it = iter(argv[1:])
    for a in it:
        if a == "--reference":
            refs.append(next(it, ""))
        elif not a.startswith("--"):
            args.append(a)
    if len(args) != 1:
        print("usage: python3 mse_style.py manuscript.docx|.md|.txt [--reference FILE ...] [--json]")
        return 2
    try:
        main_profile = profile(read_text(args[0]))
        ref_profiles = [profile(read_text(r)) for r in refs]
    except (OSError, KeyError, zipfile.BadZipFile, ElementTree.ParseError) as exc:
        print(f"cannot read input: {exc}")
        return 2
    if main_profile is None:
        print("no prose paragraphs found")
        return 2
    found = flags(main_profile)
    if as_json:
        print(json.dumps({"profile": main_profile, "flags": [{"check": c, "message": m} for c, m in found],
                          "references": ref_profiles, "result": "flags" if found else "clean"},
                         ensure_ascii=False, indent=2))
        return 1 if found else 0
    p = main_profile
    print(f"{p['language'].upper()} prose: {p['words']} words, {p['sentences']} sentences")
    rows = [("mean sentence, words", "mean_sentence_words"), ("variation of length (CV)", "cv_sentence_length"),
            ("share of long sentences", "long_sentence_share"), ("author voice (мы/we)", "author_voice"),
            ("semicolons / 1000 words", "semicolons_per_1000"), ("spaced dashes / 1000 words", "dashes_per_1000"),
            ("parentheses / 1000 words", "parentheses_per_1000"), ("nominalizations / 100 words", "nominalizations_per_100")]
    header = "| metric | manuscript |" + "".join(f" reference {k + 1} |" for k in range(len(ref_profiles)))
    print("\n" + header + "\n|---|---|" + "---|" * len(ref_profiles))
    for label, key in rows:
        cells = [str(p[key])] + [str(r[key]) if r else "—" for r in ref_profiles]
        print(f"| {label} | " + " | ".join(cells) + " |")
    print(f"\n{len(found)} flag(s)" + (":" if found else " — the prose has no machine-style markers above the limits"))
    for check, msg in found:
        print(f" - [{check}] {msg}")
    if p["long_sentences"]:
        print("\nLongest sentences to split:")
        for s in sorted(p["long_sentences"], key=lambda s: -len(s.split()))[:3]:
            print(f" - ({len(s.split())} words) {_short(s)}")
    if p["shared_5grams_abstract_conclusions"]:
        print("\nRepeated from the abstract: " + "; ".join(p["shared_5grams_abstract_conclusions"][:4]))
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
