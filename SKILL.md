---
name: scientific-editor
description: "Editor and pre-submission auditor for scientific texts in Russian and English: journal articles (Scopus, WoS, ВАК), conference volumes, theses. Two-level source verification (claim to source, source to reality); never invents data. Gates A–D (sources, internal facts, provenance and conflicts of interest incl. AI-use disclosure, falsifiability), venue-calibrated rubric with a 10-point summary and an editorial recommendation. Modes: audit-only (default; no text changes without consent), edit, pre-submission, review-edits (judge another model's or a co-author's changes). Bundled stdlib tools: a GOST-aware formatting linter for .docx/.md/.txt and a version diff that flags new numbers, new citations and excluded terms. Use when asked to check, audit, rate, edit or compare versions of a manuscript, including in Russian: проверь статью, оцени по 10-балльной шкале, отредактируй рукопись, разбери правку, сравни версии."
license: CC-BY-4.0
metadata:
  version: "4.8"
  skill-author: Rigjita Baldanova
  last-reviewed: "2026-10-24"
---

# Scientific Editor (v4.8)

> **Provenance.** v3.4 drafted by an AI sparring partner (Gemini), including formatting tooling and a Python linter. v4.0 (Muse): +Gates C/D, anchored rubric, source-access protocol. v4.1: bugfix (dangling dimension reference), restored Appendix T. v4.2: shipped tested mse_lint.py, parametrized Gate C threshold. v4.3: structural redesign after two independent model reviews (DeepSeek, Opus 5.5). v4.4: refinements from the v4.3 re-review — operationalized 'undisclosed/downplayed', stacking rule for dimension caps, auditor override mechanism, specified pilot threshold. v4.5: resolved the pilot/threshold-table inconsistency. v4.6: Gate C disclosure baseline grounded in COPE core practices and the ICMJE framework. v4.7: review-driven hardening — tabulated thresholds, evidence standard for affiliated-commercial, Gate A FAIL recommendation, Gate D operational test, disclosure checklist, linter scope note. v4.8 (Claude): usability release — stable skill name, consent-first default mode, review-edits mode with a diff tool, report template, 10-point summary, AI-use disclosure check, GOST-aware linter with .docx input, unit tests and CI. Empirically piloted once on a real co-authored manuscript (n=1 pilot, not a validation study — see Validation). The skill structures an audit; it does not replace the auditor's domain competence.

## 0. Setup & Principles
- **Verified facts only:** Never invent numbers, conditions, dates, or citations. Use `[НЕТ ДАННЫХ]` if a parameter is missing.
- **Two-level verification:** Level 1 — claim matches its cited source (fidelity). Level 2 — the source itself is independent and trustworthy (provenance). A claim that passes Level 1 but fails Level 2 is flagged, not passed.
- **Consent before edits:** the default mode is `audit-only`. Change the manuscript text only when the user explicitly asks for `edit` or `pre-submission`; never rewrite the user's or a third party's files on your own initiative. Propose, then wait.
- **Scope lock:** Edit what is present; propose additions in the report, do not widen the text. Exception: Gate D `Hypothesis:` labels are mandatory insertions, not scope violations.
- **Excluded content stays excluded:** terms, objects, or figures the author has removed (the Intake `forbid` list) are never reintroduced, in any mode.
- **Venue rules win:** Match the requested journal or conference guidelines verbatim.
- **No silent trust:** If a source cannot actually be checked (no upload, no browsing), mark the claim `[НЕ ПРОВЕРЕНО]` — never pass it quietly.
- **Rule precedence (highest first):** venue rules → gate verdicts → Appendix T formatting. When two rules conflict, the higher wins; record the conflict in the report.
- **Auditor override:** a domain expert may override any gate verdict by writing the rationale into the audit report. The override changes the verdict for scoring and recommendation purposes; the original verdict and the rationale stay on record — an override answers a flag, never deletes it.

## 1. Workflow
1. **Intake Card** (section 0 of [`assets/report_template.md`](assets/report_template.md)): venue, genre, **mode** ∈ {`audit-only` (default — report, no text changes), `edit` (apply polishing), `pre-submission` (full pass), `review-edits` (judge changes between two versions — see 1b)}, language, limits, `forbid` list (content the author has excluded). **Source-access method:** (a) user uploads sources, (b) browsing available, (c) citations on trust. Default is (c) — with every unchecked claim flagged `[НЕ ПРОВЕРЕНО]`. Note: under mode (c), Level-2 provenance checks are limited to what the manuscript itself discloses — state this limitation in the report.
2. **Claim-Evidence Matrix:** one row per numerical or causal claim: claim | source cited | Level-1 verdict | Level-2 verdict | provenance class. Cover every claim; this matrix is the denominator for Gate C.
3. **Gate A (Sources):** Verify every cited source in the matrix exists and actually supports its claim. **Verdicts:** PASS (all support), FLAG (minor mismatches — e.g., claim slightly broader than source), FAIL (phantom citation or source contradicts claim).
4. **Gate B (Internal Facts):** Check math, unit conversions, physics/chemistry consistency, cross-document consistency. **Verdicts:** PASS / FLAG (isolated slips) / FAIL (systematic errors or a load-bearing falsehood).
5. **Gate C (Provenance & COI):** Classify every quantitative claim's data as `independent` (third-party/literature) / `author-research` (authors' own experimental data — **normal science, excluded from the COI numerator**) / `affiliated-commercial` (data from the authors' employer or company, used to support commercial-adjacent claims). **COI trigger (all three must hold):** (a) quantitative claims rest on `affiliated-commercial` data above threshold, (b) no independent replication or validation is cited, (c) the commercial interest is undisclosed or downplayed — operationally: `undisclosed` = no COI/funding statement where the venue requires one, or the commercial affiliation absent from authors, acknowledgments, and funding notes; `downplayed` = affiliation disclosed only in fine print, a supplement, or another venue-invisible location while headline quantitative claims rest on the affiliated data, or the data described as "independent" anywhere in the text. **Threshold** (share by *count* of quantitative claims in the matrix) — record the chosen value:

| Venue | Threshold |
|---|---|
| Default | 50% |
| Q1 journal | 30% |
| Conference volume | 70% |

**Evidence standard:** classify data as `affiliated-commercial` when any of the following is present: employer/company name in the author byline or affiliations; a funding statement naming the company; author patent holdings covering the claimed technology. If none is present but affiliation is suspected, mark `[НЕТ ДАННЫХ]` and treat the data as `independent` for scoring — suspicion alone never triggers the gate.
**Disclosure baseline:** interpret 'undisclosed/downplayed' against COPE (Committee on Publication Ethics) core practices on competing interests and the ICMJE disclosure framework. When the venue's own COI policy is stricter than this gate, the venue wins (rule precedence). Apply these checks:
- COI/funding statement present where the venue requires one;
- commercial affiliation visible in byline, acknowledgments, or funding notes;
- affiliated data never described as "independent" in the text;
- company role in study design / data ownership stated, or marked `[НЕТ ДАННЫХ]`;
- **use of generative AI disclosed:** the manuscript names the AI models or tools used and what they were used for, and lists no AI tool as an author (COPE position statement "Authorship and AI tools", 2023; ICMJE Recommendations, 2023 update). A protocol or workflow name alone is not a disclosure. A missing or tool-less AI disclosure is a Gate C FLAG with a required fix; on its own it does not fire the COI trigger.

**Effect:** trigger fires → cap **Argumentation & data rigor (dimension 2)** at 2/5 **and** mark the manuscript structurally Q1-ineligible on provenance grounds (do not average this away against the Q1 bar).
6. **Gate D (Falsifiability):** Flag speculation presented as conclusion. **Operational test:** if the mechanism predicts the *same* observation under mutually exclusive outcomes, it is non-falsifiable → mark `[НЕФАЛЬСИФИЦИРУЕМО]`; if it predicts *different* observations that current data cannot yet distinguish, it is merely broad → require explicit `Hypothesis:` labeling and pass the gate with FLAG. **Verdicts:** PASS / FLAG (labeled but overreaching) / FAIL (unlabeled speculation presented as conclusion).
7. **Score & Audit:** Apply venue-calibrated anchored rubric below (1–5). Apply gate→score mapping: Gate A FAIL → dimension 7 capped at 2/5; Gate B FAIL → dimensions 2 and 4 capped at 2/5; Gate C trigger → dimension 2 capped at 2/5 (+ Q1-ineligible); Gate D FAIL → dimension 2 capped at 3/5. **Stacking:** when several gates cap the same dimension, the lowest cap applies; every trigger is recorded in the report. **10-point summary:** when the user asks for a score out of 10, report Overall × 2 (one decimal) and always show the seven 1–5 dimension scores beside it.
8. **Polishing** (modes `edit`, `pre-submission` only): 5 passes — (i) remove clutter, (ii) verb vitality (nominalizations → verbs), (iii) vary rhythm, (iv) terminology consistency, (v) reader-expectation structure (Gopen & Swan: familiar/old information first in each sentence, new/stress-worthy information at the end). Log every change (where → before → after → why).
9. **Delivery:** structured audit report following [`assets/report_template.md`](assets/report_template.md) — per-gate verdicts (PASS / FLAG / FAIL), dimensional scores, **editorial recommendation** ∈ {`accept`, `minor revision`, `major revision`, `reject`} — derived as: all PASS + dims ≥ venue bar → accept; FLAGs only → minor revision; any single FAIL (including Gate A FAIL alone, e.g. a phantom citation) → major revision; Gate C trigger + Gate B FAIL, or fabricated data → reject. In `edit` and `pre-submission` modes also deliver the formatted manuscript (Appendix T). Every remaining `[НЕТ ДАННЫХ]` / `[НЕ ПРОВЕРЕНО]` carries a named next action (author / editor).

### 1b. Review-edits mode
For judging changes another model or a co-author made to a base version.
1. Run `python3 mse_diff.py base.docx edited.docx --forbid "term1,term2"` (the `forbid` list from Intake). It lists every changed sentence and flags **NEW NUMBER**, **NEW CITATION**, and **FORBIDDEN** terms, plus the change in length. If the tool cannot run, compare the versions manually with the same three flags.
2. For each change decide **accept / accept with fix / reject**, with a one-line reason. Classify it: wording, structure, new fact, deletion.
3. Every new number and every new citation is a new claim: it goes through Gates A–C before it can be accepted. A number from the author's company or an unpublished business document counts as `affiliated-commercial`.
4. Forbidden content is rejected unless the author lifts the exclusion.
5. Check the edited version against the venue limit (pages or characters); a gain in style that breaks the limit is not an improvement.
6. Deliver section R of the report template: the change table, the count of accepted and rejected changes, and the recommended base for the next round.

## 2. Rubric Dimensions (1–5, anchored)

1. **Originality & novelty** — 1: no new claim, recompilation. 3: incremental advance or novel synthesis. 5: new mechanism/method/finding that shifts how the field thinks.
2. **Argumentation & data rigor** — 1: key claims unsupported or contradicted by shown data. 3: mostly supported, minor gaps. 5: every key claim backed by appropriate data with uncertainties.
3. **Literature coverage** — 1: foundational work missing. 3: adequate, minor gaps. 5: comprehensive incl. competing frameworks.
4. **Methodology & analytical reliability** — 1: irreproducible or absent methods. 3: reproducible with effort. 5: fully reproducible, appropriate statistics.
5. **Clarity, density & flow** — 1: hard to follow. 3: readable, some clutter. 5: precise, dense, well-structured.
6. **Academic/practical impact** — 1: negligible. 3: useful to specialists. 5: likely to influence practice or the field.
7. **Technical & citation accuracy** — 1: errors in math, units, or citations. 3: minor slips. 5: clean.

**Interpolation:** 2 = near the 1-anchor with one mitigating factor; 4 = meets the 5-anchor except for isolated gaps.

**Venue calibration:** conference volume (РИНЦ/ВАК): 3/5 per dimension acceptable. Q2 journal: 4/5 on dimensions 2, 4, 7 required. Q1 journal: 4+/5 on all, 5/5 on 2 and 4. ВАК thesis: 4/5 on 2, 3, 4, 7. Unlisted venue: use the nearest tier and record the choice. **Overall** = mean of the seven dimensions (and × 2 for the 10-point summary); compare against the venue bar alongside the editorial recommendation.

## 3. Validation (single-case pilot, Oct 2026)

Applied once (under v4.0 rules) to a real co-authored conference manuscript in environmental biotechnology. The manuscript is not identified here, to protect the co-authors; the audit record is kept by the skill author.
- **Gate C** fired: the affiliated-commercial share of quantitative claims exceeded the then-applied flat 50% threshold, with no independent validation and an understated commercial interest → dimension 2 capped at 2/5, manuscript marked Q1-ineligible on provenance. Under current rules the conference-volume threshold is 70%; re-running the pilot under current rules is an open item.
- **Gate B** caught a physical-interpretation error and headline figures computed outside the stated operating range.
- **Gate D** marked the central mechanistic claim `[НЕФАЛЬСИФИЦИРУЕМО]`.
- Dimensional scores agreed with two independent frontier-model reviews of the same manuscript. This agreement is a calibration signal only — model consensus is not evidence of ground-truth accuracy. Scores were far below a formatting-focused review, indicating that the gates check substance, not presentation.
- **Tooling check (v4.8):** on a 7-page RU/EN conference manuscript with a GOST reference list, the previous linter reported 60 findings, nearly all false (UDC code, dates, version numbers, English abstract, GOST-numbered references); the v4.8 linter reports none, and still catches the seeded errors in the unit tests. On a real review-edits case, `mse_diff.py` flagged every reintroduced commercial figure and excluded term.
- **Limitations:** n=1; single domain; the pilot has not been replicated. Treat the gates as structured hypotheses awaiting further pilots.

## Appendix T. Formatting & tooling

- **References:** minimal conformance pattern per GOST R 7.0.5-2008 — numbered citations [1], [2] in order of first appearance; list entries as `Author(s). Title // Source. Year. Т. Vol. № No. С. Pages.` For full bibliographic records follow GOST R 7.0.100-2018; venue rules override both.
- **Russian-language manuscripts:** decimal separator is the comma (3,14 — not 3.14); non-breaking space between number and unit (5 мг/л, 220 °C); quotation marks «…».
- **`mse_lint.py`** (standard library only): `python3 mse_lint.py manuscript.docx` (also `.md`, `.txt`; `--json` for machine output). Exit 0 = clean, 1 = findings, 2 = unreadable file. Checks: (1) citations in order of first use, no gaps, ranges like [3–5] expanded; (2) every cited [N] has a reference-list entry and every entry is cited — GOST lists (`1. …`) and bracketed lists (`[1] …`) under «Список источников», «Список литературы», «Литература», «Библиографический список» or «References»; (3) decimal points in Russian text; (4) digits glued to Cyrillic units or °C; (5) straight quotes in Russian text. It skips the reference list for checks 3–5, English-language lines, the УДК/UDC line, dates, version and licence numbers (v2.2, CC BY 4.0), DOIs, URLs and inline HTML. Also prints the length in characters. Scope: formatting only. A clean lint run is not a substantive pass and never substitutes for Gates A–D. If the linter cannot run, check the same five items by hand.
- **`mse_diff.py`** (standard library only): `python3 mse_diff.py base edited [--forbid "a,b"] [--json]` — changed sentences as a table, NEW NUMBER / NEW CITATION / FORBIDDEN flags, length change. Exit 1 when anything is flagged. It lists changes; the decision on each one is the editor's (section 1b).
- **Tests:** `python3 tests/test_tools.py` (synthetic fixtures only; run on every push by GitHub Actions).
- **Delivery check:** no `[НЕТ ДАННЫХ]` or `[НЕ ПРОВЕРЕНО]` may remain without a named next action.

## 4. Changelog
- **v4.8:** stable skill name `scientific-editor` (version moved to metadata); consent-first default (`audit-only`) and `forbid` list; `review-edits` mode with `mse_diff.py`; report template in `assets/`; 10-point summary rule; AI-use disclosure added to the Gate C checklist; linter rewritten — GOST reference lists, `.docx` input, citation ranges, no false alarms on UDC, dates, versions, English text, DOIs and URLs; unit tests and CI; pilot description de-identified.
- **v4.7:** tabulated Gate C thresholds; evidence standard for `affiliated-commercial`; Gate A FAIL → major revision stated; Gate D falsifiability operational test; COPE/ICMJE disclosure checklist; linter scope disclaimer.
- **v4.6:** COPE/ICMJE disclosure baseline for Gate C.
- **v4.5:** pilot threshold inconsistency resolved honestly (v4.0 flat rule noted; re-run open); override affects scoring/recommendation with full audit trail.
- **v4.4:** operational 'undisclosed/downplayed' criteria, stacking rule (lowest cap wins), auditor override with on-record rationale, pilot threshold specified.
- **v4.3:** structural redesign after two independent model reviews (DeepSeek, Opus 5.5): Gate C redesigned (author-research excluded from COI numerator; trigger = commercial data + no independent validation + undisclosed interest; denominator fixed to claim counts); gate verdict semantics (PASS/FLAG/FAIL per gate with score mapping); editorial recommendation (accept/minor/major/reject); rule precedence; Mode defined; Gate A contradiction resolved; venue calibration extended (theses, unlisted venues); interpolation guidance; validation limitations stated explicitly.
- **v4.2:** +working mse_lint.py (tested on clean/dirty fixtures), Gopen & Swan gloss, Gate C threshold parametrized by venue.
- **v4.1:** bugfix — Gate C and Validation now reference the existing dimension (Argumentation & data rigor, #2) instead of a non-existent "Honesty"; restored Appendix T (GOST R 7.0.5-2008 formatting, RU decimal conventions, mse_lint.py companion reference) dropped in v4.0.
- **v4.0:** +Gate C (Provenance & COI), +Gate D (Falsifiability), anchored rubric, source-access protocol with `[НЕ ПРОВЕРЕНО]` rule, provenance block, empirical validation.
- **v3.4:** baseline (Gates A/B, unanchored 1–5 rubric, formatting tooling, mse_lint.py).
