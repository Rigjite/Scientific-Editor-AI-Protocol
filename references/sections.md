# Sections — how each part of a paper works

Each section is described by its **moves** — the steps a reader expects in that order. Moves are what to say; the wording stays the author's (SKILL.md §1c). Examples are synthetic.

## Title

- Name the result or the object and the method, not a vague theme. «Расчистка дна без перехвата стоков не выводит городское озеро из гипертрофии» says more than «К вопросу об улучшении состояния водоёмов».
- Avoid empty openers: «К вопросу о…», «Некоторые аспекты…», «Исследование возможности…», "A study of…", "Towards…".
- Put the key term early; no abbreviations unless universally known.

## Abstract / аннотация

Moves: **context (1 sentence) → gap or aim → method → main result with a number → meaning.** Limits and form: references/genres.md §6. The abstract is written last and is never copied into the conclusions.

## Keywords

3–15 words or phrases (ГОСТ Р 7.0.7-2021, §4.11); terms a colleague would search for, not words already in the title.

## Introduction — Swales's CARS model

1. **Establish the territory:** why the topic matters, what is known — with citations, briefly.
2. **Establish the niche:** what is missing, contradictory or untested — the gap, stated plainly («однако…», «остаётся неизвестным…», "however…", "it remains unclear…").
3. **Occupy the niche:** the aim, and what this paper does («Цель работы — …», «Мы проверили…», "We test…"); optionally the main result in one sentence.

An introduction without move 2 reads as a textbook; without move 3 the reader does not know what the paper is for.

## Methods

- Enough for a competent colleague to repeat the work: object and site, period, sampling, instruments and calibration, statistics with software and version.
- Cite standard methods instead of describing them; describe in full only what is new.
- Past tense; the authorial «мы» is normal in Russian scientific style.

## Results

- In the order of the questions; each paragraph starts with its finding, then the numbers.
- Numbers with units and uncertainty (mean ± SD, n, interval); figures and tables carry the detail, the text carries the point.
- No interpretation and no literature here — that is the Discussion.

## Discussion — moves

1. **Main finding** in one or two sentences, without repeating the Results' numbers.
2. **Comparison** with other work: agrees, differs, and why («согласуется с…», «в отличие от…», "consistent with…", "unlike…").
3. **Explanation:** the most plausible mechanism, labeled as a hypothesis where the data cannot decide (Gate D).
4. **Limitations:** what could change the conclusion, stated by the authors before the reviewer does.
5. **Implications:** what follows for practice or for the next study.

## Conclusions / выводы

- Russian venues: numbered findings, each one sentence or two, each a result plus its consequence.
- Answer "so what?"; never restate the abstract (mse_style.py flags five-word repeats).
- No new data, no citations, no promises the paper does not support.

## Stance — how sure to sound (after Hyland 1998)

| Evidence | RU | EN |
|---|---|---|
| Direct, replicated | показано, установлено, измерено | we show, we found |
| Strong but indirect | указывает на, свидетельствует о | indicates, points to |
| Plausible, untested | по-видимому, вероятно, можно предположить; `Hypothesis:` | likely, may, we suggest; `Hypothesis:` |
| Speculation | only in the Discussion, labeled as such | idem |

Boosters («несомненно», «очевидно», "clearly", "undoubtedly") need evidence that would convince a sceptic; otherwise delete them. Never raise certainty in the voice pass.

## Back matter

Acknowledgments and funding; author contributions and conflicts of interest where the venue asks (ГОСТ Р 7.0.7-2021 lists them); **AI-use disclosure naming the tools and what they were used for** (Gate C).

## Sources

- Swales J.M. *Genre Analysis: English in Academic and Research Settings.* Cambridge University Press, 1990 (the CARS model).
- Hyland K. *Hedging in Scientific Research Articles.* John Benjamins, 1998.
- Gopen G.D., Swan J.A. The science of scientific writing. *American Scientist* 1990, 78(6), 550–558.
- ГОСТ Р 7.0.7-2021; ГОСТ Р 7.0.99-2018 (see references/genres.md).
