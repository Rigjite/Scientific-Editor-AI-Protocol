# Scientific Editor — AI Protocol

[![tests](https://github.com/Rigjite/Scientific-Editor-AI-Protocol/actions/workflows/tests.yml/badge.svg)](https://github.com/Rigjite/Scientific-Editor-AI-Protocol/actions/workflows/tests.yml)
![version 5.0](https://img.shields.io/badge/version-5.0-blue)
[![Agent Skill](https://img.shields.io/badge/Agent_Skill-agentskills.io-6f42c1)](https://agentskills.io)
![Python 3.9+, standard library only](https://img.shields.io/badge/python-3.9%2B_stdlib_only-3776AB)
[![License: CC BY 4.0](https://img.shields.io/badge/license-CC_BY_4.0-lightgrey)](LICENSE)

**Author:** Rigjita Baldanova, Ph.D. ([ORCID 0009-0009-7891-7007](https://orcid.org/0009-0009-7891-7007))\
**Domain:** AI-assisted scientific editing and pre-submission audit | Bilingual (EN/RU) | Clinical & biotech documentation

An Agent Skill that writes, edits and audits scientific texts in Russian and English — journal articles and reviews (Scopus, WoS, ВАК), conference theses (тезисы), extended abstracts, theses — without inventing data. It checks every claim against its source and the source against reality, runs four gates, scores the text against the bar of the target venue, and returns a structured report with an editorial recommendation. The full instructions are in [`SKILL.md`](SKILL.md).

## What it checks

| Gate | Question | Verdicts |
|---|---|---|
| A. Sources | Does every cited source exist and support its claim? | PASS / FLAG / FAIL |
| B. Internal facts | Are the math, units, physics and cross-references consistent? | PASS / FLAG / FAIL |
| C. Provenance & COI | Do quantitative claims rest on the authors' own company data without independent validation or proper disclosure? Is AI use disclosed with the tools named? | PASS / FLAG / trigger |
| D. Falsifiability | Is speculation presented as a conclusion? | PASS / FLAG / FAIL |

Seven rubric dimensions (1–5, anchored) are calibrated to the venue: a РИНЦ conference volume, a ВАК thesis, a Q2 or a Q1 journal. On request the overall score is also given out of 10 (mean × 2), always next to the seven dimension scores.

**Modes:** `audit-only` (default — a report, no changes to the text), `draft` (write a first draft from the author's own material), `edit`, `pre-submission`, and `review-edits` — judging changes that another model or a co-author made to a base version.

**Draft mode (v5.0).** The author gives the core in their own words — the main result in one sentence, why it matters, what is new, what is not yet known (dictation is fine). The skill builds the genre's outline ([`references/genres.md`](references/genres.md): article, review, conference theses, extended abstract, poster) with the moves of each section ([`references/sections.md`](references/sections.md): Swales's CARS introduction, discussion moves, ГОСТ abstracts, how sure to sound), waits for approval, drafts while keeping the author's sentences, and marks what only the author can supply as `[АВТОР: …]`. It never invents numbers, results or citations. Every draft ends with three before → after pairs from the author's own material, so the author learns the pattern.

**Voice pass (v4.9).** Academic text written with AI help often reads as machine-made: no author in it, three thoughts glued into one sentence with semicolons and dashes, chains of nouns where a verb would do, and conclusions that repeat the abstract. The voice pass rewrites toward classic academic style — the author shows the reader what the author has seen, precisely and in proportion to the evidence — and checks afterwards that no number or citation changed. It is about clear human prose, not about hiding AI use: AI assistance stays disclosed.

*Synthetic example:*

> **Before.** Экономический эффект складывается из отказа от мер с кратковременным эффектом, превращения затрат на вывоз ила в ресурс для земледелия и сопоставления стоимости мер с предотвращённым ущербом.
>
> **After.** Главную экономию даёт отказ от мер, которые помогают ненадолго, — ещё до того, как они оплачены. Ил, который иначе пришлось бы вывозить, может стать удобрением для полей. Стоимость каждой меры мы сравниваем с ущербом, который она предотвращает.

## Install

The skill folder must be named `scientific-editor` — the `name` in `SKILL.md` — whatever this repository is called.

- **Claude Code:** `git clone https://github.com/Rigjite/Scientific-Editor-AI-Protocol ~/.claude/skills/scientific-editor`
- **Claude app (claude.ai, desktop, mobile):** download the zip from the latest release (the folder inside is named correctly), or zip the folder yourself so that `scientific-editor/SKILL.md` sits at the top of the archive, and upload it as a custom skill in the app's skills settings. If you used v4.7 (`my-scientific-editor-v4-7`), replace it with this one.
- **Other Agent Skills clients:** copy the folder into the client's skills directory.

## Quick start

Ask in plain language, for example:

- «Проверь статью по scientific-editor: конференция РИНЦ, режим audit-only, лимит 8 страниц. Оцени по 10-балльной шкале.»
- «Разбери правку: база — v9.docx, правка соавтора — v9.1.docx. Запрещено возвращать: коммерческие цифры, названия объектов X и Y.»
- «Убери машинный стиль: режим edit, проход «голос», факты не трогать; покажи три пары «было → стало».»
- «Напиши тезисы для конференции (2 страницы, РИНЦ) по моим заметкам: главное — …»
- «Режим draft: научная статья, 8 страниц; вот мои данные и надиктовка. Сначала покажи план.»
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
python3 mse_genre.py manuscript.docx --genre article      # also: review, theses, extended-abstract

# voice: author's "we", sentence rhythm, glued clauses, noun chains, stock phrases, abstract-conclusions repetition
python3 mse_style.py manuscript.docx --reference my_own_paper_2003.docx

# unit tests (synthetic fixtures; also run by GitHub Actions on every push)
python3 tests/test_tools.py
```

The linter skips what is not Russian body text — the reference list, English lines, the УДК line, dates, version and licence numbers, DOIs, URLs — so a clean manuscript comes back clean. It checks formatting only; a clean run never replaces Gates A–D.

## Validation and limits

The gates were piloted once, on a real co-authored conference manuscript (not identified, to protect the co-authors): Gates B, C and D fired as designed, and the scores agreed with two independent frontier-model reviews — a calibration signal, not proof of accuracy. n = 1, one domain, not replicated. The skill structures an audit; it does not replace the auditor's domain competence. Details: section 3 of [`SKILL.md`](SKILL.md).

## Origins: the clinical documentation protocol

The skill grew out of a structured, multi-stage prompt-engineering and audit protocol for regulated documentation. In regulated clinical laboratories (FDA, CLIA, CAP, GLP/GMP) and academic research, documentation accuracy is non-negotiable; standard LLM prompting often introduces subtle factual drift, unverified claims, or regulatory non-compliance. The protocol accelerates scientific writing, diagnostic test directory creation, technical reports, and manuscript preparation while enforcing a strict hallucination-mitigation policy.

### The 4-stage verification pipeline

```text
[Stage 1: Source Grounding] -> [Stage 2: Structural Audit] -> [Stage 3: Fact & Metric Verification] -> [Stage 4: Regulatory & Venue Polish]
```

1. **Strict source grounding (anti-hallucination guardrail).** The AI agent is prohibited from extrapolating numerical data, p-values, Z-factors, assay sensitivity metrics, or citations not explicitly present in the primary laboratory notebook (ELN/LIMS) or source dataset. Any missing experimental parameter triggers a `[DATA_REQUIRED]` flag rather than speculative text.
2. **Methodological and statistical coherence audit.** Every assay mentioned in Results (ELISA, Western blot, FRET-HTS, PCR, HPLC, fluorescence microscopy) must have its reagents, instrument calibration and controls defined in Methods; statistical reporting must be consistent (SD vs. SEM, replicate count n, GraphPad Prism / STATISTICA model specifications).
3. **Clinical and laboratory compliance check (CLIA / CAP / GLP).** Pre-analytical clarity of specimen collection, transport and test-utilization guidance in clinical test directories; standard structure for analytical method validation summaries, turnaround-time workflows and cross-departmental scientific communication.
4. **Bilingual academic and executive calibration (EN / RU).** Removes machine-translation artifacts and enforces domain terminology across English and Russian scientific standards (peer-reviewed journals, NIH-NCATS progress reports, international environmental biotechnology specifications).

### Production prompt template: hallucination-mitigation scientific auditor

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

### Where the protocol comes from

- **Research documentation:** applied during antibacterial drug discovery research (Rutgers University) to streamline data synthesis and NIH-NCATS collaborator reporting.
- **Clinical operations:** principles derived from managing 150+ clinical diagnostic assay launches and 200+ physician/biotech accounts in CLIA/CAP-regulated reference laboratories.

### Data governance for clinical and regulated inputs

This protocol assumes it runs **only** on data the operator is authorized to process. Before any document enters the pipeline:

- **De-identification first.** No protected health information (PHI), patient identifiers, or site-identifying details enter the model context. De-identify per HIPAA Safe Harbor / Expert Determination (or the applicable local regime) *before* Stage 1.
- **No training on inputs.** Use enterprise / zero-retention API instances only — endpoints contractually excluded from model training. Consumer chatbots are not acceptable for regulated or unpublished material.
- **Unpublished data & IP.** Manuscripts, ELN/LIMS extracts, and assay validation data are processed only with the data owner's written authorization; employer and collaborator agreements govern what may leave the institutional boundary.
- **Audit trail.** Every run logs: source document hash, model ID and version, the prompt template version, and the `[DATA_REQUIRED]` / `[UNVERIFIED CLAIM]` flags raised. The log — not the chat history — is the record of what was checked.

### Worked example (illustrative excerpt)

*The passage below is a synthetic illustration of the audit format, not a real document.*

**Input (Methods excerpt, flawed):**
> "MICs were determined by broth microdilution. Briefly, bacteria were grown overnight and diluted to an appropriate density. Compound X was tested at various concentrations and growth inhibition was measured at OD600."

**Audit output:**
- **Score: 4/10.** Critical red flags: no medium specified (CAMHB required per CLSI M07); "appropriate density" is not a specification — final inoculum must be ~5×10⁵ CFU/mL per well; endpoint defined as OD600 reduction instead of absence of visible growth; no controls mentioned.
- **[UNVERIFIED CLAIM: Requires Source Data]** — "various concentrations" (exact range not stated); "measured at OD600" (no wavelength/time given).
- **Polished rewrite:** "MICs were determined by broth microdilution per CLSI M07. E. coli ATCC 25922 was grown overnight on non-selective agar; colonies were suspended to 0.5 McFarland (~1.5×10⁸ CFU/mL) and diluted 1:100 in cation-adjusted Mueller-Hinton broth (CAMHB). Compound X was serially diluted 2-fold in CAMHB (final range [DATA_REQUIRED] µg/mL); wells were inoculated to a final density of ~5×10⁵ CFU/mL, incubated at 35 ± 2 °C for 16–20 h, and read as the lowest concentration with no visible growth. Sterility (medium-only) and growth (compound-free) controls were included on each plate."

## Citation

Use GitHub's **Cite this repository** button (from [`CITATION.cff`](CITATION.cff)), or:

Baldanova, R. (2026). *Scientific Editor — AI Protocol* (Agent Skill, v5.0).\
<https://github.com/Rigjite/Scientific-Editor-AI-Protocol>

## License

[CC BY 4.0](LICENSE).

## Author

Rigjita Baldanova, Ph.D. — Ph.D. Biologist & Scientific Project Manager | AI Systems Evaluator\
LinkedIn: <https://linkedin.com/in/rigjita-baldanova>
