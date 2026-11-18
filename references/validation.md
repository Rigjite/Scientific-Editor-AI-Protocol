# Validation — what has been tested on real texts

Moved from `SKILL.md` §3 in v5.2; the summary stays there.

## Pilot on a real manuscript (October 2026, v4.0 rules)

Applied once (under v4.0 rules) to a real co-authored conference manuscript in environmental biotechnology. The manuscript is not identified here, to protect the co-authors; the audit record is kept by the skill author.
- **Gate C** fired: the affiliated-commercial share of quantitative claims exceeded the then-applied flat 50% threshold, with no independent validation and an understated commercial interest → dimension 2 capped at 2/5, manuscript marked Q1-ineligible on provenance. Under current rules the conference-volume threshold is 70%; re-running the pilot under current rules is an open item.
- **Gate B** caught a physical-interpretation error and headline figures computed outside the stated operating range.
- **Gate D** marked the central mechanistic claim `[НЕФАЛЬСИФИЦИРУЕМО]`.
- Dimensional scores agreed with two independent frontier-model reviews of the same manuscript. This agreement is a calibration signal only — model consensus is not evidence of ground-truth accuracy. Scores were far below a formatting-focused review, indicating that the gates check substance, not presentation.
- **Tooling check (v4.8):** on a 7-page RU/EN conference manuscript with a GOST reference list, the previous linter reported 60 findings, nearly all false (UDC code, dates, version numbers, English abstract, GOST-numbered references); the v4.8 linter reports none, and still catches the seeded errors in the unit tests. On a real review-edits case, `mse_diff.py` flagged every reintroduced commercial figure and excluded term. On the same manuscript, `mse_style.py` (v4.9) raised seven markers of machine-style prose: no authorial voice, about 12 semicolons and 16 spaced dashes per 1000 words, 7.7 nominalizations per 100 words, and 20 five-word phrases repeated between the abstract and the conclusions.
- **Limitations:** n=1; single domain; the pilot has not been replicated. Treat the gates as structured hypotheses awaiting further pilots.

## v5.2 tools on the author's manuscripts (17 November 2026)

- **Material:** two Russian-language conference manuscripts by the author on one subject (no text from them is reproduced here). A: 1 828 words of body prose, a conceptual paper with numbered thematic sections. B: 1 173 words, Introduction – Methods – Results and discussion – Conclusions, hedged claims. The tools excluded the English abstracts and the reference lists.
- **Before tuning:** `mse_style.py` — A 7 flags, B 1; `mse_genre.py --genre article` — A 5 flags, B clean; `mse_lint.py` — both clean.
- **Every flag checked by hand.** Confirmed in A: no authorial voice (the author is named in the third person), parenthetical clauses, nominal density 7,2 per 100 words, stock phrases (7 hits), no Methods / Results / Discussion headings. False: three «repeated opener» flags in A on the prepositions «в», «для», «при» — topic-first openers that rule 5 of the voice pass recommends; «no Introduction» and «no Conclusions» in A — the headings were numbered and had subtitles; the stock flag in B — one correct «является» in 1 173 words. Missed: overclaims in A (a conceptual model that «proves», a risk reduced «to zero», «exceptional» reliability); an Introduction in A that never states the aim; incomplete reference records in A (no pages or article number, no DOI) passed the linter.
- **Fixes:** see `references/tools.md`, «Fixed after the first run». Each has a regression test; seven of the eight new tests fail on the previous code.
- **After tuning:** `mse_style.py` — A 4 flags, all confirmed by hand, B none; `mse_genre.py` — A 5 flags (three missing headings, the aim move, overclaims), B clean; `mse_lint.py` — A 7 incomplete records, B clean. False-positive check of the new overclaim phrases on four English PubMed abstracts on lake restoration: no hits.
- **Limits:** two texts, one author, one subject, one language. Nominal density barely separates A and B (7,2 and 7,0 per 100 words), so on these texts it is a weak marker. Contrast frames, summary tails, split predicates, attributions without a citation and uniform paragraphs did not occur in either text and remain tested on synthetic fixtures only. Gates A–D were not re-run on these manuscripts. The applied genres (`references/genres-applied.md`) are not yet piloted.

## Language check (v5.2, 17 November 2026)

- **Russian:** `mse_grammar.py` on the same two manuscripts. A: 2 findings, both real (a compound adjective split by a space, a double space). B: none. The four grammar errors found by reading A (two agreement errors, a glued word, a split compound) are mostly beyond the script, as expected: only the split compound was caught.
- **Japanese:** every rule fires on a synthetic text built to contain each slip (tests). No findings on four published Japanese texts on lake sediments (two J-STAGE abstracts, a university thesis abstract, a government research summary), which use 「，」「．」 or 「、」「。」 consistently. No real Japanese manuscript with known errors has been tried, so the rate of missed slips is unknown.
- **Limits:** the script needs no dictionary and checks no agreement or government; the reading in §1e remains the check.
