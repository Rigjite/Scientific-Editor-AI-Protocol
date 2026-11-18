#!/usr/bin/env python3
"""
mse_style.py — style and voice diagnostics for the scientific-editor skill
(voice pass, section 1c of SKILL.md). Python standard library only.

Measures the markers that make academic prose read as template-driven, in
Russian or English, and points to the exact sentences:
  * author voice      — authorial "мы / наш" or "we / our" in the body;
  * sentence rhythm   — mean length, variation (CV), share of very long sentences;
  * glued clauses     — semicolons, spaced dashes and parenthetical clauses of four
                        or more words per 1000 words (glosses such as «(ЦД)» and
                        «(рис. 1)» are not counted);
  * noun chains       — nominalization density (канцелярит, "zombie nouns");
  * stock phrases     — flagged from 2 per 1000 words: Russian
                        bureaucratic clichés and English style words
                        with excess frequency in recent PubMed abstracts
                        (Kobak et al. 2025);
  * contrast frames   — «не просто X, а Y», "not just X but Y", repeated;
  * summary tails     — paragraphs that end on «Таким образом…», "Overall, …";
  * vague attribution — «исследования показывают», "studies show" with no citation;
  * split predicates  — «провести анализ», "perform an analysis" instead of the verb;
  * uniform layout    — every paragraph about the same length;
  * self-repetition   — five-word phrases shared by the abstract and the conclusions;
  * repeated openers  — the same first word at the start of many sentences
                        (prepositions, conjunctions and articles are not counted);
The catalogue behind these markers, with replacements: references/voice.md.
With --reference FILE (one or more texts whose style the author wants to
match, e.g. the author's own published papers) the same metrics are
computed for the reference and shown side by side.

Thresholds are editorial heuristics for classic academic prose, not norms:
a flag is a prompt to look. The markers say nothing about who wrote a text;
this tool is not an authorship detector and must not be presented as one.

Usage:
  python3 mse_style.py manuscript.docx [--reference my_2003_paper.docx ...] [--impersonal] [--json]
  --impersonal  the venue's register is impersonal (ГОСТ reports, standards):
                no flag for a text without «мы» / "we"
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
from mse_lint import is_japanese, is_russian, read_text, split_references  # noqa: E402

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
    "stock_per_1000": (2.0, 2.0),
    "contrast_frames": (3, 3),
    "summary_tails": (2, 2),
    "summary_tail_share": (0.3, 0.3),
    "split_predicates": (3, 3),
    "min_paragraph_cv": (0.2, 0.2),
    "paragraphs_for_cv": (6, 6),
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
           r"\bобеспечива\w+ (?:возможность|снижение|повышение)\b", r"\bуникальн\w+", r"\bинновационн\w+",
           r"\bв современном мире\b", r"\bв эпоху (?:цифров\w+|глобализаци\w+|перемен|больших данных|искусственного интеллекта|информаци\w+)",
           r"\bне секрет,? что\b", r"\bнельзя не отметить\b", r"\b(?:важно|необходимо|стоит|следует) подчеркнуть\b",
           r"\bв заключение (?:можно|следует|стоит|хочется) (?:сказать|отметить)\b", r"\bподводя итог\w*",
           r"\bимеет место\b", r"\bв целях\b", r"\bвыше(?:указанн|упомянут|изложенн|перечисленн)\w*",
           r"\bкомплексн\w+ подход\w*", r"\bширок\w+ спектр\w*", r"\bоткрыва\w+ (?:новые )?(?:возможности|горизонты|перспективы)\b",
           r"\bмногогранн\w+", r"\bдавайте\b", r"\bключев\w+ (?:значение|аспект\w*|фактор\w*)\b"],
    "en": [r"\bdelv(?:e|es|ed|ing)\b", r"\bunderscor(?:e|es|ed|ing)\b", r"\bshowcas(?:e|es|ed|ing)\b",
           r"\bcrucial\b", r"\bpivotal\b", r"\bintricate\b", r"\bnotably\b", r"\bcomprehensive\b",
           r"\badditionally\b", r"\binsights?\b", r"\bit is (?:important|worth) (?:to note|noting)\b",
           r"\bplays? a (?:crucial|key|pivotal|vital) role\b", r"\bin the realm of\b", r"\ba testament to\b",
           r"\bin today'?s (?:fast-paced |rapidly (?:changing|evolving) |ever-changing )?world\b", r"\bever-(?:evolving|changing)\b",
           r"\bnavigat\w* the (?:complexit\w+|intricacies|landscape)\b", r"\btapestry\b",
           r"\b(?:unlock|harness)\w* the (?:full )?(?:potential|power)\b", r"\bgame[- ]chang\w+", r"\bin conclusion\b",
           r"\bit is worth mentioning\b", r"\blet'?s (?:dive|delve|explore)\b", r"\bdive (?:deep )?into\b",
           r"\bseamless(?:ly)?\b", r"\bparadigm shift\b"],
}
FRAMES = {
    "ru": [r"\bне (?:просто|только|лишь)\b[^.!?;]{1,100}?(?:,|\s[–—])\s*(?:а|но и|но)\b",
           r"\bне столько\b[^.!?;]{1,100}?,\s*сколько\b",
           r"\bэто не\b[^.!?;]{1,60}?(?:,|\s[–—])\s*(?:а|это)\b"],
    "en": [r"\bnot (?:just|only|merely|simply)\b[^.!?;]{1,100}?\bbut\b",
           r"\b(?:it'?s|this is|that'?s) not\b[^.!?;]{1,60}?(?:[,;:]|\s[–—-])\s*(?:it'?s|this is|that'?s)\b"],
}
SUMMARY_OPENER = {
    "ru": r"^\W*(?:таким образом|итак|в целом|в итоге|подводя итог\w*|в заключение|резюмируя|следовательно|в конечном сч[её]те)\b",
    "en": r"^\W*(?:thus|overall|in summary|in conclusion|to sum up|to summari[sz]e|ultimately|in short|taken together|all in all|in essence)\b",
}
VAGUE = {
    "ru": r"\b(?:исследования|исследователи|уч[её]ные|эксперты|специалисты|многие авторы|литературные данные)\s+(?:\w+\s+)?"
          r"(?:показывают|показали|свидетельствуют|считают|отмечают|утверждают|доказали|подтверждают|сходятся)\b"
          r"|\bпо (?:мнению|данным) (?:многих )?(?:экспертов|уч[её]ных|специалистов|исследователей)\b|\bкак (?:известно|показывает практика)\b",
    "en": r"\b(?:studies|research|researchers|experts|scientists|the literature)\s+(?:\w+\s+)?"
          r"(?:show|shows|have shown|has shown|suggest|suggests|indicate|indicates|agree|confirm|confirms)\b"
          r"|\bit is (?:widely|well|generally) (?:known|accepted|recognized|recognised)\b",
}
CITATION = re.compile(r"\[\d|\(\s*[A-ZА-ЯЁ][^()]{0,80}?\b(?:19|20)\d\d[a-z]?\s*[;,)]|\bet al\.|\bи др\.")
SPLIT = {
    "ru": r"\b(?:провод|провед|осуществл|производ|произвед|выполн|оказыва|оказа)\w*\s+(?:\w+\s+)?"
          r"(?:анализ|оценк|контрол|мониторинг|расч[её]т|сравнени|исследовани|изучени|наблюдени|измерени|обработк|"
          r"отбор|влияни|воздействи|проверк|испытани|апробаци|корректировк|модернизаци)\w*",
    "en": r"\b(?:perform|performs|performed|performing|conduct|conducts|conducted|conducting|carr(?:y|ies|ied|ying) out|"
          r"undert(?:ake|akes|ook|aking))\s+(?:an?\s+|the\s+)?(?:\w+\s+)?"
          r"(?:analysis|analyses|assessment|evaluation|comparison|investigation|measurements?|examination|review)\b",
}
ABSTRACT = re.compile(r"^\W*(аннотация|резюме|abstract|summary)\b", re.I)
KEYWORDS = re.compile(r"^\W*(ключевые слова|keywords?)\b", re.I)
CAPTION = re.compile(r"^\W*(рисунок|рис\.|таблица|figure|fig\.|table)\s*\d", re.I)
BACK_MATTER = re.compile(r"^\W*(конфликт интересов|благодарност|финансирование|acknowledg|funding|conflicts? of interest|competing interests|author contributions)", re.I)
CONCLUSIONS = re.compile(r"^\W*(?:\d+(?:\.\d+)*\.?\s*)?(выводы(?: и заключение)?|заключение(?: и выводы)?|conclusions?|concluding remarks)\W*$", re.I)
FUNCTION_WORDS = {  # topic-first openers («В сухой сезон…») follow old-before-new; they are not a template
    "ru": {"в", "во", "на", "с", "со", "по", "при", "для", "из", "от", "до", "к", "ко", "о", "об", "у", "за",
           "под", "над", "между", "через", "после", "перед", "без", "и", "а", "но"},
    "en": {"the", "a", "an", "in", "on", "at", "for", "of", "to", "by", "with", "from", "as", "during", "after", "before"},
}
FIG_TAB = re.compile(r"\s*(рис|табл|fig|table)", re.I)


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
        if re.match(r"^\W*(УДК|UDC)\b", stripped):
            continue
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
        if first and first not in FUNCTION_WORDS[lang]:
            openers[first] = openers.get(first, 0) + 1
    spans = sorted((m.start(), m.end(), m.group(0)) for pattern in FRAMES[lang]
                   for m in re.finditer(pattern, text, re.I))
    frames, last_end = [], -1
    for start, end, found in spans:  # one frame matched by two patterns counts once
        if start >= last_end:
            frames.append(found)
            last_end = end
    split = [m.group(0) for m in re.finditer(SPLIT[lang], text, re.I)]
    body_prose = [p for p in prose if p in body]
    tails = 0
    for p in body_prose:
        ps = [s for s in sentences([p]) if len(s.split()) >= 3]
        if len(ps) >= 2 and re.match(SUMMARY_OPENER[lang], ps[-1], re.I):
            tails += 1
    vague = [s for s in sents if re.search(VAGUE[lang], s, re.I) and not CITATION.search(s)]
    para_lengths = [len(p.split()) for p in body_prose]
    para_cv = (round(statistics.pstdev(para_lengths) / statistics.mean(para_lengths), 2)
               if len(para_lengths) >= LIMITS["paragraphs_for_cv"][i] else None)
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
        "author_voice": sum(1 for m in re.finditer(VOICE[lang], text, re.I) if m.group(0) != "US"),  # not the country
        "semicolons_per_1000": round(1000 * text.count(";") / words, 1),
        "dashes_per_1000": round(1000 * len(re.findall(r"\s[–—]\s", text)) / words, 1),
        "parentheses_per_1000": round(1000 * len([c for c in re.findall(r"\(([^()]*)\)", text)
                                                 if len(c.split()) > 3 and not FIG_TAB.match(c)]) / words, 1),
        "stock_per_1000": round(1000 * len(stock_hits) / words, 1),
        "nominalizations_per_100": round(100 * len(nominal_hits) / words, 1),
        "stock_phrases": stock_hits,
        "contrast_frames": frames,
        "summary_tails": tails,
        "body_paragraphs": len(body_prose),
        "vague_attributions": vague,
        "split_predicates": split,
        "paragraph_cv": para_cv,
        "shared_5grams_abstract_conclusions": shared,
        "top_openers": sorted(openers.items(), key=lambda kv: -kv[1])[:3],
    }


def flags(p, impersonal=False):
    i = 0 if p["language"] == "ru" else 1
    out = []
    if p["author_voice"] == 0 and p["words"] >= 400 and not impersonal:
        out.append(("voice", "no authorial 'мы/наш' ('we/our') in the body: the text has no author "
                              "(if the venue's register is impersonal, rerun with --impersonal)"))
    if p["long_sentence_share"] > LIMITS["long_sentence_share"][i]:
        out.append(("rhythm", f"{int(100 * p['long_sentence_share'])} % of sentences are longer than "
                              f"{LIMITS['long_sentence_words'][i]} words — split them"))
    if p["cv_sentence_length"] < LIMITS["min_cv"][i]:
        out.append(("rhythm", f"sentence lengths are monotonous (CV {p['cv_sentence_length']}) — mix short and long"))
    for key, name in (("semicolons_per_1000", "semicolons"), ("dashes_per_1000", "spaced dashes"),
                      ("parentheses_per_1000", "parenthetical clauses (4+ words)")):
        if p[key] > LIMITS[key][i]:
            out.append(("glue", f"{p[key]} {name} per 1000 words (above {LIMITS[key][i]}) — clauses are glued together"))
    if p["nominalizations_per_100"] > LIMITS["nominalizations_per_100"][i]:
        out.append(("nouns", f"{p['nominalizations_per_100']} nominalizations per 100 words — turn nouns back into verbs"))
    if p["stock_phrases"] and p["stock_per_1000"] >= LIMITS["stock_per_1000"][i]:
        counts = {}
        for s in p["stock_phrases"]:
            counts[s.lower()] = counts.get(s.lower(), 0) + 1
        out.append(("stock", "stock phrases: " + ", ".join(f"«{k}» ×{v}" for k, v in counts.items())))
    if len(p["contrast_frames"]) >= LIMITS["contrast_frames"][i]:
        out.append(("frames", f"{len(p['contrast_frames'])} contrast frames («не просто X, а Y», 'not just X but Y') "
                              "— state the positive claim directly"))
    if (p["summary_tails"] >= LIMITS["summary_tails"][i]
            and p["summary_tails"] >= LIMITS["summary_tail_share"][i] * max(p["body_paragraphs"], 1)):
        out.append(("tails", f"{p['summary_tails']} of {p['body_paragraphs']} paragraphs end on a summary sentence "
                             "(«Таким образом…», 'Overall, …') — end on the most specific point"))
    if p["vague_attributions"]:
        out.append(("attribution", f"{len(p['vague_attributions'])} attribution(s) with no citation "
                                   "(«исследования показывают…», 'studies show…') — cite the source or cut (Gate A)"))
    if len(p["split_predicates"]) >= LIMITS["split_predicates"][i]:
        out.append(("verbs", f"{len(p['split_predicates'])} split predicates («провести анализ», 'perform an analysis') "
                             "— use the verb"))
    if p["paragraph_cv"] is not None and p["paragraph_cv"] < LIMITS["min_paragraph_cv"][i]:
        out.append(("layout", f"paragraph lengths are uniform (CV {p['paragraph_cv']}) — let length follow content"))
    if len(p["shared_5grams_abstract_conclusions"]) >= LIMITS["shared_5grams_abstract_conclusions"][i]:
        out.append(("repeat", f"{len(p['shared_5grams_abstract_conclusions'])} five-word phrases repeat between "
                              "the abstract and the conclusions — conclusions should answer 'so what?', not restate"))
    for word, n in p["top_openers"]:
        if n >= LIMITS["same_opener"][i]:
            out.append(("openers", f"{n} sentences start with «{word}»"))
    return out


def _cell(value):
    return "—" if value is None else str(value)


def _short(s, n=110):
    return s if len(s) <= n else s[: n - 1] + "…"


def main(argv):
    args, refs, as_json, impersonal = [], [], "--json" in argv, "--impersonal" in argv
    it = iter(argv[1:])
    for a in it:
        if a == "--reference":
            refs.append(next(it, ""))
        elif not a.startswith("--"):
            args.append(a)
    if len(args) != 1:
        print("usage: python3 mse_style.py manuscript.docx|.md|.txt [--reference FILE ...] [--impersonal] [--json]")
        return 2
    try:
        main_profile = profile(read_text(args[0]))
        ref_profiles = [profile(read_text(r)) for r in refs]
    except (OSError, KeyError, zipfile.BadZipFile, ElementTree.ParseError) as exc:
        print(f"cannot read input: {exc}")
        return 2
    if main_profile is None:
        lines = read_text(args[0])
        if sum(is_japanese(l) for l in lines) > len([l for l in lines if l.strip()]) / 2:
            print("Japanese text: the word-based markers of this tool do not apply (not applicable, not clean). "
                  "Run mse_grammar.py and the language check (references/language.md §3).")
            return 0
        print("no prose paragraphs found")
        return 2
    found = flags(main_profile, impersonal)
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
            ("parenthetical clauses (4+ words) / 1000 words", "parentheses_per_1000"), ("stock phrases / 1000 words", "stock_per_1000"), ("nominalizations / 100 words", "nominalizations_per_100"),
            ("summary tails (paragraphs)", "summary_tails"), ("paragraph-length CV", "paragraph_cv")]
    header = "| metric | manuscript |" + "".join(f" reference {k + 1} |" for k in range(len(ref_profiles)))
    print("\n" + header + "\n|---|---|" + "---|" * len(ref_profiles))
    for label, key in rows:
        cells = [_cell(p[key])] + [_cell(r[key]) if r else "—" for r in ref_profiles]
        print(f"| {label} | " + " | ".join(cells) + " |")
    print(f"\n{len(found)} flag(s)" + (":" if found else " — the prose has no template markers above the limits"))
    for check, msg in found:
        print(f" - [{check}] {msg}")
    if p["long_sentences"]:
        print("\nLongest sentences to split:")
        for s in sorted(p["long_sentences"], key=lambda s: -len(s.split()))[:3]:
            print(f" - ({len(s.split())} words) {_short(s)}")
    if p["vague_attributions"]:
        print("\nAttributions without a citation:")
        for s in p["vague_attributions"][:3]:
            print(f" - {_short(s)}")
    if p["shared_5grams_abstract_conclusions"]:
        print("\nRepeated from the abstract: " + "; ".join(p["shared_5grams_abstract_conclusions"][:4]))
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
