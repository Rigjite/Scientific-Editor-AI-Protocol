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
  grant              grant application: aims, significance, novelty, approach,
                     risks and alternatives, work plan, expected results; hype words
  report             research report (отчёт о НИР, ГОСТ 7.32-2017): реферат,
                     содержание, введение, заключение, list of sources; the
                     реферат's volume line, 5–15 keywords (§5.3.2.1), length (§5.3.2)
  popsci             popular-science article: the source named, the uncertainty
                     stated, no hype words, no causal or human claims from
                     correlational or animal data left unqualified
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
  python3 mse_genre.py manuscript.docx --genre article|review|theses|extended-abstract|grant|report|popsci
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
from mse_diff import sentences  # noqa: E402
from mse_lint import is_japanese, read_text, split_references  # noqa: E402

GENRES = ("article", "review", "theses", "extended-abstract", "grant", "report", "popsci")
HEADINGS = {
    "introduction": r"(введение|актуальность\b.*|introduction|background|はじめに|緒言|序論|背景)",
    "methods": r"(материалы? и метод\w*|метод\w*( исследования)?|методика\w*|materials and methods|methods?|methodology"
               r"|材料(と|および|及び)方法|(実験|調査|研究|解析|分析)?方法)",
    "results": r"(результаты( исследования)?( и (их )?обсуждение)?|results( and discussion)?|結果((と|および|及び)考察)?)",
    "discussion": r"(обсуждение( результатов)?|discussion|результаты и (их )?обсуждение|results and discussion"
                  r"|考察|結果(と|および|及び)考察)",
    "conclusions": r"(выводы( и заключение)?|заключение( и выводы)?|conclusions?|concluding remarks|結論|まとめ|おわりに|結語)",
}
CUES = {
    "citation": r"(\[\d|（[^）]{0,40}\d{4}[a-z]?）)",
    "gap": r"(однако|\bно\b|\bпока\b|требу(ет|ют)\b|не хватает|отсутству|открыт\w* вопрос|остаётся|остается|не (изучен|исследован|известн|ясн|проверен)|мало (изучен|известно)|недостаточно|неизвестн|пробел"
           r"|however|\bbut\b|\byet\b|remains? (unclear|unknown|untested)|little is known|lack of|\bgap\b|unexplored|untested"
           r"|しかし|一方|未解明|明らかでない|明らかになっていない|不明|知られていない|検討されていない|課題)",
    "aim": r"(цель(ю)? (работы|исследования|статьи|доклада)|задач[аи] (работы|исследования)|мы (проверили|предлагаем|оценили|сравнили|показываем|изучили)"
           r"|the aim|we aim|this (study|paper|work) (aims|examines|tests|proposes)|we (test|propose|examine|assess)"
           r"|本研究(では|の目的)|目的(とする|とした|は)|明らかにする)",
    "comparison": r"(согласуется|в отличие от|соответствует (данным|результатам)|подтверждает|противоречит|как и в работ"
                  r"|consistent with|in contrast|unlike|agrees with|similar to|contrary to|と一致|と同様|と異なり|と比較して|に比べ)",
    "limitations": r"(ограничени|не учитыва|не позволяет|неопределённост|неопределенност|limitation|caveat|does not account|cannot rule out"
                   r"|限界|制約|今後の課題|検討の余地|不確実性|不確かさ)",
    "implications": r"(следует(?!\s+(отметить|подчеркнуть))|рекоменд|предлагаем|позволит|первоочередн|для практики|implication|recommend|we suggest|should|next step|future work"
                    r"|示唆|今後|必要である|提案する|提言|応用)",
    "selection": r"(отобран|поиск публикаций|запрос|баз[аеу] данных|pubmed|scopus|web of science|google scholar|включали|критери"
                 r"|searched|search (terms|strategy)|inclusion|検索|データベース|J-STAGE|CiNii|対象とした|選定)",
    "methods": r"(метод|отобран|измер|использовал|проанализирова|проб[аы]|наблюдени|method|measured|sampled|analy[sz]ed|we used"
               r"|測定|採取|分析し|用いた|実施し|調査し|実験)",
    "conclusion": r"(вывод|следовательно|таким образом|итак|conclude|conclusion|therefore|thus|結論|以上より|したがって|以上の結果)",
}
ABSTRACT = re.compile(r"^\W*(аннотация|резюме|abstract|要旨|要約|抄録)(?:\b|(?=[\W]|$))[.:：\s]*", re.I)
KEYWORDS = re.compile(r"^\W*(ключевые слова|keywords?|キーワード)(?:\b|(?=[\W]|$))[.:：\s]*", re.I)
FILLER = re.compile(r"^(в (данной |настоящей )?(статье|работе) (рассматрива|анализиру|описыва|излага)|автор\w* (статьи )?(рассматрива|анализиру)"
                    r"|this (paper|article) (discusses|deals with|is devoted))", re.I)
TITLE_OPENERS = re.compile(r"^(к вопросу|некоторые (аспекты|вопросы|проблемы)|об? одном|исследование возможности|a study of|towards?\b|on the question)", re.I)
STANDARD_PAGE = 1800
GRANT_MOVES = (
    ("aims", r"(цел[ьию]\b|задач[аиу]|specific aims?|objectives?|\baims?\b)", "no aims or objectives"),
    ("significance", r"(актуальн|значимост|важн|significance|importance|matters|problem|gap)", "no statement of why the work matters"),
    ("novelty", r"(новизн|нов(?:ый|ая|ое|ые) (?:подход|метод)|впервые|innovation|novel|state of the art|beyond)", "no statement of what is new"),
    ("approach", r"(метод|подход|approach|methods?|methodology|research (?:design|strategy)|work packages?)", "no approach or methods"),
    ("risks", r"(риск|альтернатив|запасн|risks?|pitfalls?|alternative|contingency|mitigat)", "no risks and alternatives"),
    ("plan", r"(план работ|календарн|этап|срок|квартал|timeline|milestones?|work plan|gantt|\byear [1-5]\b|\bmonths? \d)", "no work plan or milestones"),
    ("outcomes", r"(ожидаем\w* результат|результаты проекта|показател|indicators?|deliverables?|expected (?:outcomes|results)|measur)", "no expected results or measures"),
)
HYPE = re.compile(r"(революцион\w*|прорывн\w*|научн\w+ прорыв\w*|прорыв\w* в (?:науке|медицине|лечении|области)|сенсаци\w*|"
                  r"не име\w+ аналогов|впервые в мире|world[- ]first|first[- ]ever|revolutionary|"
                  r"breakthrough(?! infection| pain| bleeding| seizure)|game[- ]chang\w*|unprecedented|paradigm[- ]shift|miracle|"
                  r"уч[её]ные доказали|scientists (?:have )?proven|"
                  r"(?<!не )доказыва\w+,? что|(?<!не )гарантиру\w+|(?<!не )полностью исключа\w+|не вызывает сомнени\w*|"
                  r"исключительн(?:ая|ую|ой|ые|ых|ый|ое|ого) (?:[^\W\d_]+ )?(?:надёжн|надежн|эффективн|точн)\w*|риск\w*[^.]{0,40}\bк нулю|"
                  r"画期的|世界初|革命的|前例のない|完全に解決|(?<!not )(?<!n't )\bproves? that|(?<!not )(?<!n't )(?<!cannot )\bguarantee[sd]?\b|eliminat\w+ (?:the |any |all )?risks?\b|beyond (?:any )?doubt)", re.I)
REPORT_HEADINGS = {
    "реферат": r"реферат",
    "содержание": r"(содержание|оглавление)",
    "введение": r"введение",
    "заключение": r"заключение",
}
REPORT_VOLUME = re.compile(r"\d+\s*(?:с\.|стр\.|страниц)", re.I)
POPSCI_SOURCE = re.compile(r"(doi|https?://|журнал\w*|опубликова\w*|статья в|published in|journal|\b(?:19|20)\d\d\b)", re.I)
POPSCI_UNCERTAINTY = re.compile(r"(пока не|неизвестн|не ясно|неясно|ограничени|не доказ|предварительн|"
                                r"ещё предстоит|еще предстоит|а не причин|не означает|"
                                r"not yet|unknown|unclear|limitation|preliminary|remains to be|does not (?:prove|mean|show))", re.I)
POPSCI_CAUSAL = re.compile(r"(вызыва\w+|привод\w+ к|излечива\w+|леч(?:ит|ат)\b|защища\w+(?:\s+\w+)?\s+от|снижа\w+ риск|"
                           r"\bcauses?\b|\bcures?\b|\bprevents?\b|protects?(?:\s+\w+)?\s+against|reduces? the risk)", re.I)
POPSCI_CORRELATIONAL = re.compile(r"(связ[ьаи]н?\w*\s+с\b|коррел\w*|ассоциирован\w*|associat\w*|linked (?:to|with)|correlat\w*)", re.I)
POPSCI_ANIMAL = re.compile(r"(на мыш\w*|на крыс\w*|на животных|в пробирке|in vitro|на клетк\w*|in mice|in rats|in animals|in cells)", re.I)
POPSCI_HUMAN = re.compile(r"(люд\w*|человек\w*|пациент\w*|\bpeople\b|\bpatients\b|\bhumans?\b)", re.I)


def classify_heading(line):
    text = line.strip().strip("#*_ ").rstrip(".:").strip()
    text = re.sub(r"^(?:[\d０-９]+(?:[.．][\d０-９]+)*[.．、]?|[IVXLC]+\.)\s*(?=\D)", "", text)  # «1. Введение», «2．方法», «II. Methods»
    if not text or len(text.split()) > 8:
        return None
    candidates = [text, re.split(r"\s*(?::|\s[—–-]\s)\s*", text, maxsplit=1)[0]]  # «Введение: подзаголовок»
    for candidate in candidates:
        for name, pattern in HEADINGS.items():
            if re.fullmatch(pattern, candidate, re.I):
                return name
    return None


def parse(lines):
    ref_at = split_references(lines)
    body = lines if ref_at is None else lines[:ref_at]
    doc = {"references": ref_at is not None, "abstracts": [], "keywords": [], "title": "", "sections": {}}
    current = None
    pending = None  # "abstract" / "keywords" when the label stands on a line of its own
    for line in body:
        stripped = line.strip()
        if not stripped:
            continue
        if (not doc["title"] and not re.match(r"^\W*(УДК|UDC)\b", stripped)
                and (len(stripped.split()) >= 3 or (is_japanese(stripped) and len(stripped) >= 8))):
            doc["title"] = stripped
            continue
        if ABSTRACT.match(stripped):
            rest = ABSTRACT.sub("", stripped, count=1).strip()
            doc["abstracts"].append(rest)
            pending = None if rest else "abstract"
            continue
        if KEYWORDS.match(stripped):
            rest = KEYWORDS.sub("", stripped, count=1)
            doc["keywords"].append([k for k in re.split(r"[;,、，；]", rest) if k.strip()])
            pending = None if rest.strip() else "keywords"
            continue
        kind = classify_heading(stripped)
        if pending and not kind:
            if pending == "abstract":  # the abstract runs until the keywords or the next heading
                doc["abstracts"][-1] = (doc["abstracts"][-1] + " " + stripped).strip()
                continue
            doc["keywords"][-1] = [k for k in re.split(r"[;,、，；]", stripped) if k.strip()]
            pending = None
            continue
        pending = None
        if kind:
            current = kind
            doc["sections"].setdefault(kind, [])
            if kind == "results" and re.search("обсуждение|discussion|考察", stripped, re.I):
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
            if is_japanese(abstract):  # Japanese limits are in characters (字) and set by the journal
                pass
            elif words > 250:
                found.append(("limits", f"abstract {i}: {words} words, more than 250 (ГОСТ Р 7.0.7-2021 §4.10)"))
            if FILLER.match(abstract.strip()):
                found.append(("limits", f"abstract {i} opens with a filler phrase (ГОСТ Р 7.0.99-2018 §5.2.3)"))
        for i, kws in enumerate(doc["keywords"], 1):
            if not 3 <= len(kws) <= 15:
                found.append(("limits", f"keywords {i}: {len(kws)} items, expected 3–15 (ГОСТ Р 7.0.7-2021 §4.11)"))
    elif genre == "grant":
        text = doc["text"]
        for _, pattern, label in GRANT_MOVES:
            if not re.search(pattern, text, re.I):
                found.append(("moves", label))
        if not re.search(r"\d", text):
            found.append(("moves", "no numbers anywhere — aims and results need measures and dates"))
    elif genre == "report":
        found += check_report(lines)
    elif genre == "popsci":
        text = doc["text"]
        if not POPSCI_SOURCE.search(text):
            found.append(("source", "the study is not named (journal, year, DOI or link)"))
        if not POPSCI_UNCERTAINTY.search(text):
            found.append(("uncertainty", "nothing says what is not yet known or what the study cannot show"))
        sents = sentences(text.splitlines())
        if POPSCI_CORRELATIONAL.search(text) and any(POPSCI_CAUSAL.search(x) for x in sents):
            found.append(("claims", "causal wording in a text about an association — 'связан с' is not 'вызывает' "
                                    "(Gate D; references/genres-applied.md §11)"))
        if POPSCI_ANIMAL.search(text) and any(POPSCI_CAUSAL.search(x) and POPSCI_HUMAN.search(x) for x in sents):
            found.append(("claims", "an animal or cell study, and a sentence promising an effect in people — "
                                    "check the inference (Gate D)"))
    else:  # theses, extended-abstract: moves by cue words, headings optional
        text = doc["text"]
        for move, label in (("aim", "no explicit aim"), ("methods", "no methods (object, period, method)"),
                            ("conclusion", "no conclusion")):
            if not has(move, text):
                found.append(("moves", label))
        res = results if results.strip() else text
        if not re.search(r"\d", res):
            found.append(("moves", "results without numbers"))

    if genre in ("grant", "popsci", "theses", "extended-abstract", "article", "review"):
        hype = sorted({m.group(0).lower() for m in HYPE.finditer(doc["text"])})
        if hype:
            found.append(("claims", "hype words: " + ", ".join(f"«{h}»" for h in hype)
                          + " — support each with evidence or cut; 'first' only after a search"))

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
               "abstract_words": [f"{len(a)} 字" if is_japanese(a) else len(a.split()) for a in doc["abstracts"]],
               "keywords_counts": [len(k) for k in doc["keywords"]], "characters": chars, "standard_pages": pages}
    return found, summary


def check_report(lines):
    """ГОСТ 7.32-2017: structural elements (§4) and the реферат (§5.3)."""
    found = []
    ref_at = split_references(lines)
    body = lines if ref_at is None else lines[:ref_at]
    heads = {}
    for i, line in enumerate(body):
        text = line.strip().strip("#*_ ").rstrip(".:").strip()
        for name, pattern in REPORT_HEADINGS.items():
            if text and len(text.split()) <= 4 and re.fullmatch(pattern, text, re.I):
                heads.setdefault(name, i)
    for name in REPORT_HEADINGS:
        if name not in heads:
            found.append(("structure", f"no «{name.upper()}» heading — ГОСТ 7.32-2017 §4 lists it among the "
                                       "structural elements; check whether this report needs it"))
    if ref_at is None:
        found.append(("structure", "no «СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ» heading"))
    if "реферат" in heads:
        start = heads["реферат"] + 1
        later = [i for i in heads.values() if i > heads["реферат"]]
        block = [l.strip() for l in body[start:min(later) if later else len(body)] if l.strip()]
        volume = [l for l in block if REPORT_VOLUME.search(l) and len(l) < 200]
        if not volume:
            found.append(("referat", "реферат: no line with the report's volume (pages, figures, tables, sources — §5.3.2)"))
        keywords = None
        for l in block:
            label = re.match(r"^\W*ключевые слова\W*", l, re.I)
            letters = [c for c in l if c.isalpha()]
            if label or (letters and sum(c.isupper() for c in letters) / len(letters) > 0.8 and "," in l):
                keywords = [k for k in re.split(r"[;,]", re.sub(r"^\W*ключевые слова\W*", "", l, flags=re.I)) if k.strip()]
                break
        if keywords is None:
            found.append(("referat", "реферат: no keyword list (5–15 words or phrases, §5.3.2.1)"))
        elif not 5 <= len(keywords) <= 15:
            found.append(("referat", f"реферат: {len(keywords)} keywords, expected 5–15 (§5.3.2.1)"))
        text = " ".join(l for l in block if l not in volume and not (keywords and ("," in l and
                        (re.match(r"^\W*ключевые слова", l, re.I) or l.upper() == l))))
        if len(text) > STANDARD_PAGE:
            found.append(("referat", f"реферат text: {len(text)} characters — the optimum is 850 printed characters, "
                                     "at most one page (§5.3.2)"))
    return found


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
