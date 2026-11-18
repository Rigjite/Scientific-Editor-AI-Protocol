# Scientific Editor — AI Protocol

[![tests](https://github.com/Rigjite/Scientific-Editor-AI-Protocol/actions/workflows/tests.yml/badge.svg)](https://github.com/Rigjite/Scientific-Editor-AI-Protocol/actions/workflows/tests.yml)
![version 5.2](https://img.shields.io/badge/version-5.2-blue)
[![Agent Skill](https://img.shields.io/badge/Agent_Skill-agentskills.io-6f42c1)](https://agentskills.io)
![Python 3.9+, standard library only](https://img.shields.io/badge/python-3.9%2B_stdlib_only-3776AB)
[![License: CC BY 4.0](https://img.shields.io/badge/license-CC_BY_4.0-lightgrey)](LICENSE)

**Author:** Rigjita Baldanova, Ph.D. ([ORCID 0009-0009-7891-7007](https://orcid.org/0009-0009-7891-7007))\
**Domain:** Scientific editing and pre-submission audit | Russian, English, Japanese | Clinical & biotech documentation

An Agent Skill that writes, edits and audits scientific and technical texts in Russian, English and Japanese, and never invents data. It covers journal articles and reviews (Scopus, WoS, ВАК), conference theses (тезисы), extended abstracts, theses and monographs; grant applications and research reports (ГОСТ 7.32); technical documentation; popular-science articles; talk and business presentations; cover letters and responses to reviewers. The skill checks every claim against its source and the source against reality, runs four gates, and scores the text against the bar of the target venue. You get a structured report with an editorial recommendation. The full instructions are in [`SKILL.md`](SKILL.md).

## What it checks

| Gate | Question | Verdicts |
|---|---|---|
| A. Sources | Does every cited source exist and support its claim? | PASS / FLAG / FAIL |
| B. Internal facts | Are the math, units, physics and cross-references consistent? | PASS / FLAG / FAIL |
| C. Provenance & COI | Do quantitative claims rest on the authors' own company data without independent validation or proper disclosure? Are the statements the venue requires in place? | PASS / FLAG / trigger |
| D. Falsifiability | Is speculation presented as a conclusion? | PASS / FLAG / FAIL |

Seven rubric dimensions (1–5, anchored) are calibrated to the venue: conference proceedings (incl. РИНЦ), a dissertation (ВАК), a Q2 or a Q1 journal. On request the overall score is also given out of 10 (mean × 2), always next to the seven dimension scores.

**Modes:** `audit-only` (default — a report, no changes to the text), `draft` (write a first draft from the author's own material), `edit`, `pre-submission`, and `review-edits` — judging changes that another model or a co-author made to a base version.

**Draft mode (v5.0).** The author gives the core in their own words — the main result in one sentence, why it matters, what is new, what is not yet known (dictation is fine). The skill builds the genre's outline ([`references/genres.md`](references/genres.md): article, review, conference theses, extended abstract, poster) with the moves of each section ([`references/sections.md`](references/sections.md): Swales's CARS introduction, discussion moves, ГОСТ abstracts, how sure to sound), waits for approval, drafts while keeping the author's sentences, and marks what only the author can supply as `[АВТОР: …]`. It never invents numbers, results or citations. Every draft ends with three before → after pairs from the author's own material, so the author learns the pattern.

**Applied genres (v5.2).** Grants, monographs, research reports, technical documentation, popular science, talks, business presentations and letters around a publication each get a shape, a voice and their own checks ([`references/genres-applied.md`](references/genres-applied.md), outlines in [`assets/outlines.md`](assets/outlines.md)). The funder's form, the publisher's rules or the customer's contract always win. For grants the skill reads the funder's rules before drafting, including any rule on AI tools: where text drafted with such tools is not accepted as the applicant's own (NIH, from the 25 September 2025 receipt date), it outlines, checks and edits the author's own text instead of writing it.

**Language check (v5.2).** After the voice pass the skill reads for grammar, spelling, punctuation and typography in Russian, English and Japanese ([`references/language.md`](references/language.md)), with facts frozen and the venue's rules first. `mse_grammar.py` catches the mechanical slips; agreement, commas and word choice need a reader. For Japanese the default norm, where the journal says nothing, is the government guide 「公用文作成の考え方」 (2022): one style, one punctuation set, one width for digits, short sentences.

**Voice pass (v4.9, extended in v5.2).** Text written in a hurry or from templates often reads as assembled rather than written: no author in it, three thoughts glued into one sentence, chains of nouns where a verb would do, «не просто X, а Y» in every paragraph, paragraphs that end on «Таким образом…», «исследования показывают» with no citation, conclusions that repeat the abstract. The voice pass rewrites toward the register of the genre — classic academic prose for a paper, plain instructions for a manual, a conversational account for popular science — and checks afterwards that no number or citation changed. The catalogue of канцелярит and template patterns, with replacements, is in [`references/voice.md`](references/voice.md). Natural does not mean invented: the skill never adds anecdotes, quotations or deliberate errors that the author did not supply. The markers say nothing about who wrote a text, and the skill never draws that conclusion.

*Synthetic example:*

> **Before.** Экономический эффект складывается из отказа от мер с кратковременным эффектом, превращения затрат на вывоз ила в ресурс для земледелия и сопоставления стоимости мер с предотвращённым ущербом.
>
> **After.** Главную экономию даёт отказ от мер, которые помогают ненадолго, — ещё до того, как они оплачены. Ил, который иначе пришлось бы вывозить, может стать удобрением для полей. Стоимость каждой меры мы сравниваем с ущербом, который она предотвращает.

## Install

The skill folder must be named `scientific-editor` — the `name` in `SKILL.md` — whatever this repository is called.

- **Claude Code:** `git clone https://github.com/Rigjite/Scientific-Editor-AI-Protocol ~/.claude/skills/scientific-editor`
- **Claude app (claude.ai, desktop, mobile):** download the source code (zip) from the latest release and rename the folder inside it to `scientific-editor` (GitHub names it after the repository and the version), or zip the folder yourself so that `scientific-editor/SKILL.md` sits at the top of the archive, and upload it as a custom skill in the app's skills settings. If you used v4.7 (`my-scientific-editor-v4-7`), replace it with this one.
- **Other Agent Skills clients:** copy the folder into the client's skills directory.

## Quick start

Ask in plain language, for example:

- «Проверь статью по scientific-editor: конференция РИНЦ, режим audit-only, лимит 8 страниц. Оцени по 10-балльной шкале.»
- «Разбери правку: база — v9.docx, правка соавтора — v9.1.docx. Запрещено возвращать: коммерческие цифры, названия объектов X и Y.»
- «Убери машинный стиль: режим edit, проход «голос», факты не трогать; покажи три пары «было → стало».»
- «Напиши тезисы для конференции (2 страницы, РИНЦ) по моим заметкам: главное — …»
- «Режим draft: научная статья, 8 страниц; вот мои данные и надиктовка. Сначала покажи план.»
- «Заявка на грант по форме фонда (прилагаю): проверь структуру и критерии, убери канцелярит, текст пишу я.»
- «Сделай научно-популярную статью по нашей работе (прилагаю) — без сенсаций, с тем, что пока неизвестно.»
- «Доклад на 12 минут: план слайдов с заголовками-утверждениями по моей статье.»
- "Audit this manuscript for a Q2 journal, pre-submission mode; sources are uploaded."

The report follows [`assets/report_template.md`](assets/report_template.md): intake card, summary with gate verdicts, claim–evidence matrix, disclosure checklist, rubric, formatting, open items, and — in review-edits mode — a per-change decision table.

## Tools (Python 3.9+, standard library only)

```bash
# formatting: citation order and gaps, reference list (GOST "1. …" or "[1] …"),
# Russian decimal commas, number–unit spacing, «…» quotes; also prints the length
python3 mse_lint.py manuscript.docx          # .docx, .md or .txt; --json for machine output

# review-edits: changed sentences, NEW NUMBER / NEW CITATION / FORBIDDEN / MISSING NUMBER flags, length change
python3 mse_diff.py base.docx edited.docx --forbid "term1,term2"

# genre: parts, Introduction and Discussion moves, abstract ≤ 250 words, 3–15 keywords, title, length
python3 mse_genre.py manuscript.docx --genre article      # also: review, theses, extended-abstract, grant, report, popsci

# voice: author's "we", rhythm, glued clauses, noun chains, stock phrases, «не просто X, а Y» frames,
# «Таким образом…» paragraph tails, "studies show" without a citation, «провести анализ», abstract-conclusions repetition
python3 mse_style.py manuscript.docx --reference my_own_paper_2003.docx

# language: words written twice, spaces, split compounds (RU); mixed styles and punctuation,
# mixed digit widths, doubled particles, ら-less forms, wordy forms, long sentences (JA)
python3 mse_grammar.py manuscript.docx

# unit tests (synthetic fixtures; also run by GitHub Actions on every push)
python3 tests/test_tools.py
```

The linter skips what is not Russian body text — the reference list, English lines, the УДК line, dates, version and licence numbers, DOIs, URLs — so a clean manuscript comes back clean. It checks formatting only; a clean run never replaces Gates A–D. All four tools work on heuristics and have known blind spots — for example, a short forbidden term can match inside a longer word; the list is in [`references/tools.md`](references/tools.md).

## Validation and limits

The gates were piloted once, on a real co-authored conference manuscript (not identified, to protect the co-authors): Gates B, C and D fired as designed, and the scores agreed with two independent frontier-model reviews — a calibration signal, not proof of accuracy. n = 1, one domain, not replicated. The voice markers and applied genres added in v5.2 are tested on synthetic fixtures only and have not yet been tried on real texts. The skill structures an audit; it does not replace the auditor's domain competence. Details: [`references/validation.md`](references/validation.md).

## Origins: the clinical documentation protocol (historical)

*This section describes the earlier, pre-skill protocol and is kept for history. Where it differs from [`SKILL.md`](SKILL.md), `SKILL.md` wins: the skill scores seven dimensions on a 1–5 scale (not four on 1–10), marks missing data as `[НЕТ ДАННЫХ]` (= `[DATA_REQUIRED]` below) and unchecked claims as `[НЕ ПРОВЕРЕНО]` (= `[UNVERIFIED CLAIM]`).*

The skill grew out of a structured, multi-stage prompt-engineering and audit protocol for regulated documentation. In regulated clinical laboratories (FDA, CLIA, CAP, GLP/GMP) and academic research, documentation accuracy is non-negotiable; standard LLM prompting often introduces subtle factual drift, unverified claims, or regulatory non-compliance. The protocol was built to speed up scientific writing, diagnostic test directory creation, technical reports and manuscript preparation, and it instructs the model to follow a strict hallucination-mitigation policy — compliance is checked by the auditor, never assumed.

### The 4-stage verification pipeline

```text
[Stage 1: Source Grounding] -> [Stage 2: Structural Audit] -> [Stage 3: Fact & Metric Verification] -> [Stage 4: Regulatory & Venue Polish]
```

1. **Strict source grounding (anti-hallucination guardrail).** The agent is prohibited from extrapolating numerical data, p-values, Z-factors, assay sensitivity metrics, or citations not explicitly present in the primary laboratory notebook (ELN/LIMS) or source dataset. Any missing experimental parameter triggers a `[DATA_REQUIRED]` flag rather than speculative text.
2. **Methodological and statistical coherence audit.** Every assay mentioned in Results (ELISA, Western blot, FRET-HTS, PCR, HPLC, fluorescence microscopy) must have its reagents, instrument calibration and controls defined in Methods; statistical reporting must be consistent (SD vs. SEM, replicate count n, GraphPad Prism / STATISTICA model specifications).
3. **Clinical and laboratory compliance check (CLIA / CAP / GLP).** Pre-analytical clarity of specimen collection, transport and test-utilization guidance in clinical test directories; standard structure for analytical method validation summaries, turnaround-time workflows and cross-departmental scientific communication.
4. **Bilingual academic and executive calibration (EN / RU).** Removes machine-translation artifacts and enforces domain terminology across English and Russian scientific standards (peer-reviewed journals, grant progress reports, international environmental biotechnology specifications).

### Original prompt template: hallucination-mitigation scientific auditor

```text
### ROLE
You are a Senior Scientific Auditor and Lead Editor specializing in Microbiology, Molecular Biology,
Clinical Diagnostics, and Aquatic & Environmental Sciences.

### HARD CONSTRAINTS (HALLUCINATION-MITIGATION PROTOCOL)
1. NEVER invent, extrapolate, or modify experimental numbers, concentrations, p-values, sample sizes,
   or literature citations.
2. Flag any claim lacking direct evidence in the provided source text with:
   [UNVERIFIED CLAIM: Requires Source Data]
3. Cross-check all assay descriptions (PCR, ELISA, FRET, MIC50, HPLC, Microscopy) for internal
   consistency between Methods and Results.

### AUDIT RUBRIC (Score 1-10 per category)
1. Scientific & Mechanistic Rigor: Are biological pathways and ecological/assay principles stated accurately?
2. Methodological Reproducibility: Are controls (positive, negative, sterility), reagents, and statistical
   tests clearly defined?
3. Regulatory & Data Integrity (GLP/CLIA): Does the terminology adhere to Good Documentation Practices?
4. Clarity & Conciseness: Remove redundant prose while preserving technical precision.

### OUTPUT FORMAT
- Section 1: Quantitative Audit Score & Critical Red Flags
- Section 2: Line-by-Line Fact & Consistency Verification Table
- Section 3: Polished, Publication-Ready Text
```

### Data governance for clinical and regulated inputs

This protocol assumes it runs **only** on data the operator is authorized to process. Before any document enters the pipeline:

- **De-identification first.** No protected health information (PHI), patient identifiers, or site-identifying details enter the model context. De-identify per HIPAA Safe Harbor / Expert Determination (or the applicable local regime) *before* Stage 1.
- **No training on inputs.** For PHI, regulated records and other people's unpublished material, use enterprise / zero-retention API instances only — endpoints contractually excluded from model training. Before using a consumer app (see Install), check its data-use settings and your institution's policy; for an author's own unpublished manuscript, the author decides.
- **Unpublished data & IP.** Manuscripts, ELN/LIMS extracts, and assay validation data are processed only with the data owner's written authorization; employer and collaborator agreements govern what may leave the institutional boundary.
- **Audit trail.** Every run logs: source document hash, model ID and version, the prompt or skill version, and the `[НЕТ ДАННЫХ]` / `[НЕ ПРОВЕРЕНО]` flags raised. The log — not the chat history — is the record of what was checked.

### Worked example (illustrative excerpt)

*The passage below is a synthetic illustration of the audit format, not a real document.*

**Input (Methods excerpt, flawed):**
> "MICs were determined by broth microdilution. Briefly, bacteria were grown overnight and diluted to an appropriate density. Compound X was tested at various concentrations and growth inhibition was measured at OD600."

**Audit output:**
- **Score: 4/10** (legacy 1–10 scale). Critical red flags: no organism, strain or medium specified (CLSI M07 uses cation-adjusted Mueller-Hinton broth, CAMHB, for non-fastidious aerobes); "appropriate density" is not a specification — the M07 target is ~5×10⁵ CFU/mL per well; the endpoint is an OD600 reduction, whereas M07 reads the MIC as the lowest concentration with no visible growth; no controls mentioned.
- **[UNVERIFIED CLAIM: Requires Source Data]** — "various concentrations" (range and dilution scheme not stated); "measured at OD600" (read time and inhibition threshold not given).
- **Rewrite skeleton** — every value the input does not contain stays a `[DATA_REQUIRED]` slot; CLSI M07 defaults appear only as prompts inside the slots and enter the text once the author confirms them: "MICs were determined by broth microdilution per CLSI M07 [DATA_REQUIRED: edition; deviations]. [DATA_REQUIRED: organism(s), strain IDs] were grown overnight on [DATA_REQUIRED: medium] and suspended to [DATA_REQUIRED: turbidity standard, e.g. 0.5 McFarland]. Compound X was diluted [DATA_REQUIRED: scheme, e.g. two-fold] in [DATA_REQUIRED: broth — M07: CAMHB] over [DATA_REQUIRED] µg/mL; wells were inoculated to [DATA_REQUIRED — M07 target ≈ 5×10⁵ CFU/mL] and incubated at [DATA_REQUIRED — M07: 35 ± 2 °C, ambient air, 16–20 h]. The MIC was read as [DATA_REQUIRED: endpoint — no visible growth per M07, or the OD600 threshold and read time actually used]. Controls: [DATA_REQUIRED: sterility (medium only), growth (compound-free), QC strain]."
- **Why a skeleton, not a finished paragraph:** this is what the skill returns when the input lacks the data. A finished paragraph would need values the author never gave — exactly what the skill forbids. Once the author fills the slots, the skeleton is the finished paragraph.

## Citation

Use GitHub's **Cite this repository** button (from [`CITATION.cff`](CITATION.cff)), or:

Baldanova, R. (2026). *Scientific Editor — AI Protocol* (Agent Skill, v5.2).\
<https://github.com/Rigjite/Scientific-Editor-AI-Protocol>\
DOI (v5.2): [10.5281/zenodo.24330003](https://doi.org/10.5281/zenodo.24330003); DOI of v5.0: [10.5281/zenodo.23627929](https://doi.org/10.5281/zenodo.23627929); all versions: [10.5281/zenodo.23627928](https://doi.org/10.5281/zenodo.23627928). Each GitHub release receives its own version DOI on Zenodo.

## License

[CC BY 4.0](LICENSE).

## Author

Rigjita Baldanova, Ph.D. — Biologist & Scientific Project Manager | AI Systems Evaluator\
ORCID: [0009-0009-7891-7007](https://orcid.org/0009-0009-7891-7007) · LinkedIn: <https://linkedin.com/in/rigjita-baldanova>
