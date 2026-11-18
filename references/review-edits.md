# Review-edits mode — full procedure

Read with `SKILL.md` §1b. Moved here from `SKILL.md` in v5.2; the summary stays in §1b.

For judging changes another model or a co-author made to a base version.
1. Run `python3 mse_diff.py base.docx edited.docx --forbid "term1,term2"` (the `forbid` list from Intake). It lists every changed sentence and flags **NEW NUMBER**, **NEW CITATION**, and **FORBIDDEN** terms, plus the change in length. If the tool cannot run, compare the versions manually with the same three flags.
2. For each change decide **accept / accept with fix / reject**, with a one-line reason. Classify it: wording, structure, new fact, deletion.
3. Every new number and every new citation is a new claim: it goes through Gates A–C before it can be accepted. A number from the author's company or an unpublished business document counts as `affiliated-commercial`.
4. Forbidden content is rejected unless the author lifts the exclusion.
5. Check the edited version against the venue limit (pages or characters); a gain in style that breaks the limit is not an improvement.
6. Deliver section R of the report template: the change table, the count of accepted and rejected changes, and the recommended base for the next round.
