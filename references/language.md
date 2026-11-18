# Language check — Russian, English, Japanese (SKILL.md §1e)

The language check is a careful reading for errors of grammar, spelling, punctuation and typography. It comes after the voice pass and before formatting, and it runs in every mode. In `audit-only` it lists the errors; in `edit` and `pre-submission` it corrects them. `mse_grammar.py` catches the mechanical slips a script can see (§4). Agreement, government, commas and word choice still need a reader.

**Rules for every language**
- **The venue's rules win.** That includes a journal's own punctuation, spelling of «ё», quotation marks and reference style. Record each choice in the report.
- **Facts are frozen.** A correction changes form, not content: no number, unit, term, name or citation changes. Run `python3 mse_diff.py before after` afterwards; any NEW NUMBER, NEW CITATION or MISSING NUMBER flag means the edit is rolled back.
- **Terms are not errors.** Check an unfamiliar term against the field before you «correct» it; a domain term in the author's spelling stays unless a source shows it is wrong.
- **Quotations stay verbatim.** Errors inside a quotation are marked [sic] (or the venue's equivalent), not corrected.
- **Deliver** section L of the report template: where → error → correction → rule, with the count by kind. In `edit` mode, give a log of every change.

## 1. Russian

Norm: «Правила русской орфографии и пунктуации. Полный академический справочник» (под ред. В. В. Лопатина, 2006). For doubtful spellings, use the academic spelling dictionary of the V. V. Vinogradov Institute of the Russian Language (orfo.ruslang.ru).

- **Agreement:** adjective and noun in gender, number and case («внешнее антропогенное воздействие»); subject and predicate («была разработана методика»); participles with the noun they qualify.
- **Government:** prepositions and cases («согласно приказу», «благодаря чему», «по завершении»); one verb governing two objects in different cases.
- **One word, two words or a hyphen:** compound adjectives («сельскохозяйственный», «научно-исследовательский», «эколого-экономический»); «пол-», «полу-», «не» with participles and adjectives.
- **Glued and split words:** two words written as one («Бейрагипертрофного»), one word split in two.
- **Punctuation:** participial and adverbial-participial phrases, parenthetical words, complex sentences, the dash between subject and predicate, homogeneous members.
- **Typography:** decimal comma, a non-breaking space between a number and its unit, «…» quotation marks («„…“» inside), the dash « — » and the hyphen. These are checked by `mse_lint.py`, Appendix T.
- **Slips:** a word written twice, missing or extra spaces, letters swapped.

## 2. English

Norm: the venue's style guide (for example the journal's instructions, AMA, APA or Chicago); keep British or American spelling consistent with the venue.

- Subject–verb agreement, especially after long noun phrases; articles (a / an / the / none) with count and mass nouns; tense consistency (methods and results in the past, established facts in the present).
- Dangling and misplaced modifiers; «which» and «that»; comparisons with «than» / «compared with».
- Hyphenated compound modifiers before a noun («a two-step model»), not after it; numbers and units by the venue's style.
- Slips: a word written twice («the the»), missing spaces, homophones (its / it's, affect / effect).

## 3. Japanese

Norm: the journal's instructions first. For general written Japanese, the skill uses 「公用文作成の考え方」 (文化審議会建議, 7 January 2022; distributed across government by a Cabinet notice of 11 January 2022). It is a guide for government documents, so in a paper it is the default only where the journal says nothing. On writing for science: 木下是雄『理科系の作文技術』 (中公新書, 1981). References follow the journal's style or SIST 02 «参照文献の書き方» (JST, 2007 revision).

- **One style.** Do not mix 常体 (だ・である) and 敬体 (です・ます) in one document; quotations, subordinate clauses and bullet lists are the exceptions (公用文作成の考え方 Ⅲ-1イ). In 常体 the guide uses the forms 「である・であろう・であった」 (Ⅲ-1ウ). Papers follow the journal's register.
- **Punctuation.** In horizontal text 「、」「。」 by default; 「，」 is also allowed; never mix the two in one document (Ⅰ-5(1)ア). Some science journals ask for 「，」「．」 — follow the journal.
- **Numbers and Latin letters.** Arabic numerals in horizontal text (Ⅰ-4ア); large numbers with a comma every three digits (Ⅰ-4イ); one width, full or half, throughout the document (Ⅰ-4エ); Latin letters in the width that suits them, consistently (Ⅰ-6エ). Follow the journal.
- **One point per sentence.** Keep sentences short; from 50–60 characters, check whether the sentence is still easy to read; move long modifiers into a sentence of their own (Ⅲ-3ア, イ).
- **Wordy forms.** 「利用することができる」 → 「利用できる」, 「調査を実施した」 → 「調査した」, 「問題があるということになる」 → 「問題がある」 (Ⅱ-5ウ(イ)); no repetition of the same meaning (Ⅱ-5ウ(ア)).
- **Directness.** Avoid double negatives unless they carry deliberate emphasis (Ⅲ-3コ). Do not use the passive where it hides who acted (Ⅲ-3ケ). Avoid phrasing that can be read two ways (Ⅲ-3シ). Give numbers and dates instead of vague degree words (Ⅱ-5イ(イ)).
- **Fact and opinion.** Separate what was observed from what the author thinks, and state facts plainly (木下 1981, chapters 6 «はっきり言い切る姿勢» and 7 «事実と意見»).
- **Standard forms.** Use the standard potential forms in formal writing: 「見られる」, 「来られる」, not the ら-less 「見れる」 and 「来れる」, which formal contexts still avoid.
- **Slips.** Doubled particles (「をを」), a wrong kanji from the input method (同音異義語: 「以外」 and 「意外」, 「保障」 and 「保証」), full-width digits mixed with half-width ones.

## 4. What the script checks (`mse_grammar.py`)

`python3 mse_grammar.py manuscript.docx [--json]`. It reads the body text and skips the reference list. It flags:
- in all three languages, a word written twice, doubled spaces, a space before a punctuation mark, and no space after a comma or semicolon;
- in Russian, compound adjectives split by a space;
- in Japanese, mixed styles, mixed 「、」「，」 or 「。」「．」, full- and half-width digits or Latin letters in one text, doubled particles, ら-less forms, wordy forms, double negatives, and sentences over 100 characters.

It does not check agreement, government, commas or word choice. A clean run means only that no mechanical slip was found.

**Optional, outside the skill:** LanguageTool can run as a local server and checks Russian and English among more than 20 languages; a Russian morphological analyser (pymorphy3) would make agreement checks possible. Neither is bundled, because the skill uses the Python standard library only. Never send an unpublished manuscript to an online checker that the author, the journal or the funder has not approved.

## Sources

- Правила русской орфографии и пунктуации. Полный академический справочник / под ред. В. В. Лопатина. М.: Эксмо, 2006. 480 с. (orfo.ruslang.ru).
- 文化審議会. 公用文作成の考え方（建議）. 2022年1月7日; 内閣官房長官通知「「公用文作成の考え方」の周知について」, 2022年1月11日 (bunka.go.jp).
- 木下是雄. 理科系の作文技術. 中央公論社 (中公新書 624), 1981.
- 科学技術振興機構. SIST 02-2007 参照文献の書き方. 2007.
- 朴宰怜. 「ら抜きことば」の発展の様相とその実態. 一橋日本語教育研究. 2015, 3号, p. 97–102.
