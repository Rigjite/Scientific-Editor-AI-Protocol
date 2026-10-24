#!/usr/bin/env python3
"""
mse_genre.py — genre and structure check for the scientific-editor skill
(draft mode §1d; references/genres.md and references/sections.md).
Python standard library only. Reads .docx / .md / .txt.

Checks that a manuscript has what its genre needs:
  article            abstract, keywords, Introduction, Methods, Results,
                     Discussion (may be merged with Results), Conclusions, references
  review             abstract, keywords, Introduction, a literature-selection
                     method, Conclusions, references
  theses             conference theses: aim, methods, results with numbers,
                     conclusion (headings optional — detected by cue words)
  extended-abstract  the same moves as theses, for an English extended abstract
and, where the genre has them, the moves inside sections:
  Introduction (Swales's CARS)  territory (citations) → gap → aim
  Discussion                    comparison with other work → limitations → implications
plus the formal limits: abstract ≤ 250 words (ГОСТ Р 7.0.7-2021 §4.10),
3–15 keywords (§4.11), no filler opening in the abstract (ГОСТ Р 7.0.99-2018
§5.2.3), title without empty openers, and length against --max-chars.
The length is also shown in standard pages (1800 characters with spaces) for
orientation only: the real page count depends on font, spacing, figures and
tables, so page limits are checked on the PDF, not here.

Cue words are heuristics: a missing move is a prompt to look, not a verdict.
The venue's own rules always win.

Usage:
  python3 mse_genre.py manuscript.docx --genre article|review|theses|extended-abstract
                       [--max-chars N] [--json]
Exit 0 = no flags, 1 = flags, 2 = input error.
"""
import json
import os
import re
import sys
import zipfile
from xml.etree import ElementTree

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mse_lint import read_text, split_references  # noqa: E402

GENRES = ("article", "review", "theses", "extended-abstract")
HEADINGS = {
    "introduction": r"(введение|актуальность\b.*|introduction|background)",
    "methods": r"(материалы? и метод\w*|метод\w*( исследования)?|методика\w*|materials and methods|methods?|methodology)",
    "results": r"(результаты( исследования)?( и (их )?обсуждение)?|results( and discussion)?)",
    "discussion": r"(обсуждение( результатов)?|discussion|результаты и (их )?обсуждение|results and discussion)",
    "conclusions": r"(выводы|заключение|conclusions?|concluding remarks)",
}
CUES = {
    "citation": r"\[\d",
    "gap": r"(однако|\bно\b|\bпока\b|требу(ет|ют)\b|не хватает|отсутству|открыт\w* вопрос|остаётся|остается|не (изучен|исследован|известн|ясн|проверен)|мало (изучен|известно)|недостаточно|неизвестн|пробел"
           r"|however|\bbut\b|\byet\b|remains? (unclear|unknown|untested)|little is known|lack of|\bgap\b|unexplored|untested)",
    "aim": r"(цель(ю)? (работы|исследования|статьи|доклада)|задач[аи] (работы|исследования)|мы (проверили|предлагаем|оценили|сравнили|показываем|изучили)"
           r"|the aim|we aim|this (study|paper|work) (aims|examines|tests|proposes)|we (test|propose|examine|assess))",
    "comparison": r"(согласуется|в отличие от|соответствует (данным|результатам)|подтверждает|противоречит|как и в работ"
                  r"|consistent with|in contrast|unlike|agrees with|similar to|contrary to)",
    "limitations": r"(ограничени|не учитыва|не позволяет|неопределённост|неопределенност|limitation|caveat|does not account|cannot rule out)",
    "implications": r"(следует|рекоменд|предлагаем|позволит|первоочередн|для практики|implication|recommend|we suggest|should|next step|future work)",
    "selection": r"(отобран|поиск публикаций|запрос|баз[аеу] данных|pubmed|scopus|web of science|google scholar|включали|критери"
                 r"|searched|search (terms|strategy)|inclusion)",
    "methods": r"(метод|отобран|измер|использовал|проанализирова|проб[аы]|наблюдени|method|measured|sampled|analy[sz]ed|we used)",
    "conclusion": r"(вывод|следовательно|таким образом|итак|conclude|conclusion|therefore|thus)",
}
ABSTRACT = re.compile(r"^\W*(аннотация|резюме|abstract)\b[.:\s]*", re.I)
KEYWORDS = re.compile(r"^\W*(ключевые слова|keywords?)\b[.:\s]*", re.I)
FILLER = re.compile(r"^(в (данной |настоящей )?(статье|работе) (рассматрива|анализиру|описыва|излага)|автор\w* (статьи )?(рассматрива|анализиру)"
                    r"|this (paper|article) (discusses|deals with|is devoted))", re.I)
TITLE_OPENERS = re.compile(r"^(к вопросу|некоторые (аспекты|вопросы|проблемы)|об? одном|исследование возможности|a study of|towards?\b|on the question)", re.I)
STANDARD_PAGE = 1800


def classify_heading(line):
    text = line.strip().strip("#*_ ").rstrip(".:").strip()
    if not text or len(text.split()) > 8:
        return None
    for name, pattern in HEADINGS.items():
        if re.fullmatch(pattern, text, re.I):
            return name
    return None


def parse(lines):
    ref_at = split_references(lines)
    body = lines if ref_at is None else lines[:ref_at]
    doc = {"references": ref_at is not None, "abstracts": [], "keywords": [], "title": "", "sections": {}}
    current = None
    for line in body:
        stripped = line.strip()
        if not stripped:
            continue
        if not doc["title"] and not re.match(r"^\W*(УДК|UDC)\b", stripped) and len(stripped.split()) >= 3:
            doc["title"] = stripped
            continue
        if ABSTRACT.match(stripped):
            doc["abstracts"].append(ABSTRACT.sub("", stripped, count=1))
            continue
        if KEYWORDS.match(stripped):
            doc["keywords"].append([k for k in re.split(r"[;,]", KEYWORDS.sub("", stripped, count=1)) if k.strip()])
            continue
        kind = classify_heading(stripped)
        if kind:
            current = kind
            doc["sections"].setdefault(kind, [])
            if kind == "results" and re.search("обсуждение|discussion", stripped, re.I):
                doc["sections"].setdefault("discussion", [])
                current = "results+discussion"
                doc["sections"].setdefault(current, [])
            continue
        if current:
            doc["sections"].setdefault(current, []).append(stripped)
    doc["text"] = "\n".join(body)
    return doc


def has(cue, text):
    return re.search(CUES[cue], text, re.I) is not None


def check(lines, genre, max_chars=None):
    doc = parse(lines)
    found = []
    sec = {k: " ".join(v) for k, v in doc["sections"].items()}
    discussion = sec.get("discussion", "") + " " + sec.get("results+discussion", "")
    results = sec.get("results", "") + " " + sec.get("results+discussion", "")

    if genre in ("article", "review"):
        needed = ["introduction", "conclusions"] + (["methods", "results", "discussion"] if genre == "article" else ["methods"])
        for part in needed:
            if part not in doc["sections"]:
                found.append(("structure", f"no '{part}' section heading"))
        if not doc["abstracts"]:
            found.append(("structure", "no abstract (Аннотация / Abstract)"))
        if not doc["keywords"]:
            found.append(("structure", "no keywords (Ключевые слова / Keywords)"))
        if not doc["references"]:
            found.append(("structure", "no reference-list heading"))
        intro = sec.get("introduction", "")
        if intro:
            for move, label in (("citation", "territory: no citations in the Introduction"),
                                ("gap", "niche: the Introduction never states what is missing (gap)"),
                                ("aim", "occupy: the Introduction never states the aim")):
                if not has(move, intro):
                    found.append(("moves", label))
        if genre == "review" and not has("selection", sec.get("methods", "") + " " + intro):
            found.append(("moves", "review: no description of how the literature was searched and selected"))
        if genre == "article" and discussion.strip():
            if not (has("comparison", discussion) or has("citation", discussion)):
                found.append(("moves", "Discussion: no comparison with other work"))
            if not has("limitations", discussion):
                found.append(("moves", "Discussion: limitations are not stated"))
            if not has("implications", discussion + " " + sec.get("conclusions", "")):
                found.append(("moves", "Discussion/Conclusions: no implications (what follows, what to do)"))
        for i, abstract in enumerate(doc["abstracts"], 1):
            words = len(abstract.split())
            if words > 250:
                found.append(("limits", f"abstract {i}: {words} words, more than 250 (ГОСТ Р 7.0.7-2021 §4.10)"))
            if FILLER.match(abstract.strip()):
                found.append(("limits", f"abstract {i} opens with a filler phrase (ГОСТ Р 7.0.99-2018 §5.2.3)"))
        for i, kws in enumerate(doc["keywords"], 1):
            if not 3 <= len(kws) <= 15:
                found.append(("limits", f"keywords {i}: {len(kws)} items, expected 3–15 (ГОСТ Р 7.0.7-2021 §4.11)"))
    else:  # theses, extended-abstract: moves by cue words, headings optional
        text = doc["text"]
        for move, label in (("aim", "no explicit aim"), ("methods", "no methods (object, period, method)"),
                            ("conclusion", "no conclusion")):
            if not has(move, text):
                found.append(("moves", label))
        res = results if results.strip() else text
        if not re.search(r"\d", res):
            found.append(("moves", "results without numbers"))

    title = doc["title"]
    if title and TITLE_OPENERS.match(title):
        found.append(("title", "title opens with an empty phrase — name the result or the object"))
    if title and len(title.split()) > 25:
        found.append(("title", f"title has {len(title.split())} words — consider a shorter one that names the result"))

    chars = len(doc["text"])
    pages = round(chars / STANDARD_PAGE, 1)
    typical = {"theses": 4, "extended-abstract": 3}.get(genre)
    if typical and not max_chars and pages > typical:
        found.append(("length", f"about {pages} standard pages — far longer than usual for {genre} "
                                "(references/genres.md); check the call for papers"))
    if max_chars and chars > max_chars:
        found.append(("length", f"{chars} characters — above {max_chars}"))
    summary = {"genre": genre, "title": title, "sections_found": sorted(doc["sections"]),
               "abstract_words": [len(a.split()) for a in doc["abstracts"]],
               "keywords_counts": [len(k) for k in doc["keywords"]], "characters": chars, "standard_pages": pages}
    return found, summary


def main(argv):
    args, genre, max_chars = [], None, None
    it = iter(argv[1:])
    try:
        for a in it:
            if a == "--genre":
                genre = next(it, "")
            elif a == "--max-chars":
                max_chars = int(next(it, ""))
            elif not a.startswith("--"):
                args.append(a)
    except ValueError:
        args = []
    if len(args) != 1 or genre not in GENRES:
        print("usage: python3 mse_genre.py manuscript --genre " + "|".join(GENRES) + " [--max-chars N] [--json]")
        return 2
    try:
        lines = read_text(args[0])
    except (OSError, KeyError, zipfile.BadZipFile, ElementTree.ParseError) as exc:
        print(f"cannot read {args[0]}: {exc}")
        return 2
    found, summary = check(lines, genre, max_chars)
    if "--json" in argv:
        print(json.dumps({"summary": summary, "flags": [{"check": c, "message": m} for c, m in found],
                          "result": "flags" if found else "clean"}, ensure_ascii=False, indent=2))
        return 1 if found else 0
    print(f"genre: {genre}; sections: {', '.join(summary['sections_found']) or '—'}; "
          f"abstract words: {summary['abstract_words'] or '—'}; keywords: {summary['keywords_counts'] or '—'}; "
          f"length: {summary['characters']} characters ≈ {summary['standard_pages']} standard pages "
          f"(orientation only — check page limits on the PDF)")
    if found:
        print(f"{len(found)} flag(s):")
        for check_name, msg in found:
            print(f" - [{check_name}] {msg}")
    else:
        print("clean — the genre's parts and moves are in place")
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
