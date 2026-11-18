#!/usr/bin/env python3
"""Unit tests for mse_lint.py, mse_diff.py, mse_style.py, mse_genre.py and mse_grammar.py (standard library only).

Run from the repository root:  python3 tests/test_tools.py
All fixtures are synthetic; no real manuscript is stored in this repository.
"""
import io
import os
import sys
import tempfile
import unittest
import zipfile
from contextlib import redirect_stdout

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import mse_diff  # noqa: E402
import mse_genre  # noqa: E402
import mse_grammar  # noqa: E402
import mse_lint  # noqa: E402
import mse_style  # noqa: E402

CLEAN = """УДК 504.455.054:004.942:574.5
ПРИМЕР СТАТЬИ
Аннотация. Концентрация фосфора составила 0,4 мг/л [1], что выше нормы [2].
Abstract. Mean phosphorus was 0.4 mg/L, and the index was 2.53 ± 1.32.
Публикации отобраны 21–22.10.2026; использован комплекс версия 2.2 (CC BY 4.0) [3–4].
Ссылка на данные: https://example.org/data/v1.2 и DOI: 10.1000/xyz.123 [4, с. 12].
Список источников
1. Иванов И.И. Статья // Журнал. 2020. Т. 1, № 2. С. 3–4.
2. Smith J. Paper // Journal. 2021. Vol. 5. P. 1.5–2.
3. Петров П.П. Книга. М., 2019. 100 с.
4. Doe J. Data set. 2022. DOI: 10.1000/xyz.123.
"""

DIRTY = """Введение
Концентрация составила 3.5 мг/л [2], при нагреве до 220°C и дозе 5мг [1].
Авторы называют это "эффектом" [4].
Список литературы
[1] Первый источник.
[2] Второй источник.
[3] Третий источник.
"""


def lint_text(text):
    return mse_lint.lint(text.splitlines())


def make_docx(path, paragraphs):
    w = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
    body = "".join(f"<w:p><w:r><w:t xml:space=\"preserve\">{p}</w:t></w:r></w:p>" for p in paragraphs)
    xml = f'<?xml version="1.0" encoding="UTF-8"?><w:document xmlns:w="{w}"><w:body>{body}</w:body></w:document>'
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("word/document.xml", xml)


class LintTests(unittest.TestCase):
    def test_clean_gost_article_has_no_findings(self):
        self.assertEqual(lint_text(CLEAN), [])

    def test_dirty_article_findings(self):
        checks = {c for c, _, _ in lint_text(DIRTY)}
        self.assertEqual(checks, {"citations", "references", "decimal", "spacing", "quotes"})

    def test_order_gap_missing_and_unused(self):
        msgs = " ".join(m for _, _, m in lint_text(DIRTY))
        self.assertIn("not sequential: [2, 1, 4]", msgs)
        self.assertIn("never cited in the text: [3]", msgs)
        self.assertIn("no reference-list entry: [4]", msgs)
        self.assertIn("listed but never cited: [3]", msgs)

    def test_spacing_catches_unit_and_degrees(self):
        found = [m for c, _, m in lint_text(DIRTY) if c == "spacing"]
        self.assertTrue(any("0°C" in m for m in found))
        self.assertTrue(any("5м" in m for m in found))

    def test_english_line_not_checked_for_decimal(self):
        self.assertEqual(lint_text("Mean value was 2.53 and 0.4 mg/L.\nСписок источников\n"), [])

    def test_versions_licenses_dates_udc_skipped(self):
        text = "УДК 574.5\nВерсия 2.2, лицензия CC BY 4.0, Python 3.9, дата 22.10.2026.\n"
        self.assertEqual(lint_text(text), [])

    def test_citation_range_and_page(self):
        self.assertEqual(mse_lint.cited_numbers("[1] [2–4] [5, с. 12] [6; 7] [et al.]"), [1, 2, 3, 4, 5, 6, 7])

    def test_missing_reference_heading(self):
        msgs = [m for _, _, m in lint_text("Текст со ссылкой [1].\n")]
        self.assertIn("reference-list heading not found", msgs)

    def test_markdown_escapes_and_docx(self):
        with tempfile.TemporaryDirectory() as d:
            md = os.path.join(d, "a.md")
            with open(md, "w", encoding="utf-8") as f:
                f.write("Текст \\[1\\].\n\n**Список источников**\n\n1\\. Источник.\n")
            self.assertEqual(mse_lint.lint(mse_lint.read_text(md)), [])
            docx = os.path.join(d, "a.docx")
            make_docx(docx, ["Значение 3.5 мг/л [1].", "Список источников", "1. Источник."])
            lines = mse_lint.read_text(docx)
            self.assertEqual(lines[0], "Значение 3.5 мг/л [1].")
            self.assertEqual([c for c, _, _ in mse_lint.lint(lines)], ["decimal"])

    def test_cli_exit_codes(self):
        with tempfile.TemporaryDirectory() as d:
            good, bad = os.path.join(d, "good.md"), os.path.join(d, "bad.md")
            for path, text in ((good, CLEAN), (bad, DIRTY)):
                with open(path, "w", encoding="utf-8") as f:
                    f.write(text)
            with redirect_stdout(io.StringIO()):
                self.assertEqual(mse_lint.main(["mse_lint.py", good]), 0)
                self.assertEqual(mse_lint.main(["mse_lint.py", bad]), 1)
                self.assertEqual(mse_lint.main(["mse_lint.py", os.path.join(d, "none.md")]), 2)


BASE = [
    "Озеро сильно загрязнено: индекс 2,4–2,5 при пороге 1 [1]. Данные получены в 2023 г.",
    "Исследователи рекомендуют расчистку дна [2]. Наблюдения провёл Р.М. Иванов на оз. Бейра.",
]
EDITED = [
    "Озеро сильно загрязнено: индекс 2.4–2.5 при пороге 1 [1]. Данные получены в 2023 г.",
    "Исследователи рекомендуют расчистку дна [2]. Наблюдения провёл Р.М. Иванов на оз. Бейра.",
    "Урожайность составит 5,5–6,2 т/га при цене 450 LKR/кг [3].",
]


class DiffTests(unittest.TestCase):
    def test_identical_versions_have_no_changes(self):
        changes, forbidden, stats = mse_diff.diff(BASE, BASE)
        self.assertEqual((changes, forbidden, stats["change_percent"]), ([], [], 0.0))

    def test_new_numbers_and_citations_flagged(self):
        changes, _, _ = mse_diff.diff(BASE, EDITED)
        added = [c for c in changes if c["kind"] == "added"]
        self.assertEqual(len(added), 1)
        self.assertEqual(added[0]["new_numbers"], ["450", "5.5", "6.2"])
        self.assertEqual(added[0]["new_citations"], [3])

    def test_decimal_separator_change_is_not_a_new_number(self):
        changes, _, _ = mse_diff.diff(BASE[:1], EDITED[:1])
        self.assertTrue(all(not c["new_numbers"] for c in changes))

    def test_missing_numbers_flagged(self):
        edited = ["Озеро сильно загрязнено [1]. Данные получены в 2023 г.", BASE[1]]
        _, _, stats = mse_diff.diff(BASE, edited)
        self.assertEqual(stats["missing_numbers"], ["1", "2.4", "2.5"])
        _, _, same = mse_diff.diff(BASE, BASE)
        self.assertEqual(same["missing_numbers"], [])

    def test_forbidden_terms(self):
        _, forbidden, _ = mse_diff.diff(BASE, EDITED, forbid=["LKR", "Котокель"])
        self.assertEqual([f["term"] for f in forbidden], ["LKR"])

    def test_abbreviations_do_not_split_sentences(self):
        sents = mse_diff.sentences([BASE[1]])
        self.assertEqual(len(sents), 2)
        self.assertTrue(sents[1].endswith("оз. Бейра."))

    def test_cli_exit_codes(self):
        with tempfile.TemporaryDirectory() as d:
            a, b = os.path.join(d, "a.txt"), os.path.join(d, "b.txt")
            for path, lines in ((a, BASE), (b, EDITED)):
                with open(path, "w", encoding="utf-8") as f:
                    f.write("\n".join(lines))
            with redirect_stdout(io.StringIO()):
                self.assertEqual(mse_diff.main(["mse_diff.py", a, a]), 0)
                self.assertEqual(mse_diff.main(["mse_diff.py", a, b]), 1)
                self.assertEqual(mse_diff.main(["mse_diff.py", a, os.path.join(d, "x.txt")]), 2)


ROBOTIC = """Аннотация. Цель работы – обоснование применения цифровых двойников для предварительной оценки хозяйственных решений и снижения ущерба окружающей среде.
Ключевые слова: цифровой двойник; оценка
Введение
Данная работа является обобщением опыта применения цифровых двойников; рассмотрение проводится в рамках концепции устойчивого развития; осуществление мониторинга является условием управления. Таким образом, внедрение двойников обеспечивает снижение затрат (на мониторинг и обследование) и повышение точности (прогнозирования и планирования) – это важно отметить для обоснования решений.
Рисунок 1 – Схема применения цифрового двойника для оценки хозяйственных решений и снижения ущерба окружающей среде в условиях неопределённости
Выводы
Цель работы – обоснование применения цифровых двойников для предварительной оценки хозяйственных решений и снижения ущерба окружающей среде достигнута; применение рекомендуется.
Конфликт интересов. Авторы заявляют об отсутствии конфликта интересов, который является формальным требованием издания и не влияет на выводы.
"""

HUMAN = """Введение
Мы начали с простого вопроса: что увидит городской водоём через десять лет, если ничего не делать? Ответ оказался неприятным. Фосфора в воде так много, что даже хороший ветланд не выведет озеро из худшего класса. Поэтому мы сравнили три пути, а не один. Каждый путь мы проверили на тех же исходных данных и с теми же порогами, чтобы сравнение было честным. Расчистка дна быстро улучшает воду, но стоки снова приносят грязь, и через несколько лет всё возвращается. Перехват стоков работает медленно, зато результат держится годами. Мы считаем, что городу нужны обе меры сразу, и показываем, во что это обойдётся.
"""


class StyleTests(unittest.TestCase):
    def test_robotic_text_is_flagged(self):
        p = mse_style.profile(ROBOTIC.splitlines())
        checks = {c for c, _ in mse_style.flags(p)}
        self.assertTrue({"glue", "nouns", "stock", "repeat"} <= checks, checks)
        self.assertEqual(p["author_voice"], 0)

    def test_human_text_is_clean(self):
        p = mse_style.profile(HUMAN.splitlines())
        self.assertEqual(mse_style.flags(p), [], p)
        self.assertGreaterEqual(p["author_voice"], 4)

    def test_voice_flag_needs_enough_text(self):
        p = mse_style.profile(ROBOTIC.splitlines())
        self.assertNotIn("voice", {c for c, _ in mse_style.flags(p)})  # too short to judge
        long_text = ROBOTIC.replace("Введение\n", "Введение\n" + ("Данная работа является обзором методов оценки. " * 60) + "\n")
        p2 = mse_style.profile(long_text.splitlines())
        self.assertIn("voice", {c for c, _ in mse_style.flags(p2)})

    def test_captions_and_back_matter_are_skipped(self):
        p = mse_style.profile(ROBOTIC.splitlines())
        self.assertFalse(any(s.startswith("Рисунок") for s in p["long_sentences"]))
        self.assertNotIn("конфликт", " ".join(p["shared_5grams_abstract_conclusions"]))

    def test_english_stock_words(self):
        text = ("Introduction\nThis study delves into lake restoration and underscores the crucial role of "
                "wetlands; notably, it offers comprehensive insights into the intricate landscape of nutrients.")
        p = mse_style.profile(text.splitlines())
        self.assertEqual(p["language"], "en")
        self.assertGreaterEqual(len(p["stock_phrases"]), 6)

    def test_cli_with_reference(self):
        with tempfile.TemporaryDirectory() as d:
            a, b = os.path.join(d, "a.md"), os.path.join(d, "b.md")
            with open(a, "w", encoding="utf-8") as f:
                f.write(ROBOTIC)
            with open(b, "w", encoding="utf-8") as f:
                f.write(HUMAN)
            buf = io.StringIO()
            with redirect_stdout(buf):
                code = mse_style.main(["mse_style.py", a, "--reference", b, "--json"])
            self.assertEqual(code, 1)
            data = __import__("json").loads(buf.getvalue())
            self.assertGreater(data["references"][0]["author_voice"], 0)
            with redirect_stdout(io.StringIO()):
                self.assertEqual(mse_style.main(["mse_style.py", b]), 0)
                self.assertEqual(mse_style.main(["mse_style.py", os.path.join(d, "none.md")]), 2)


ARTICLE = """УДК 574.5
Расчистка дна без перехвата стоков не выводит городское озеро из гипертрофии
Аннотация. Городское озеро сильно загрязнено. Мы сравнили три сценария восстановления и показали, что только сочетание мер даёт устойчивый результат.
Ключевые слова: озеро; эвтрофирование; расчистка; ветланды
Введение
Эвтрофирование городских озёр хорошо описано [1, 2]. Однако эффект сочетания мер для мелких озёр тропиков не изучен. Цель работы — сравнить сценарии восстановления.
Материалы и методы
Мы использовали опубликованные данные 80 проб за 2022–2023 гг. [3].
Результаты
Индекс загрязнения составил 2,5 при пороге 1,0.
Обсуждение
Результат согласуется с данными [4]. Ограничение работы — отсутствие данных о составе ила. Следует начать с анализа ила.
Выводы
1. Только сочетание мер даёт устойчивое улучшение.
Список источников
1. А. 2. Б. 3. В. 4. Г.
"""

THESES_OK = """Ветланды не выводят городское озеро из гипертрофии
Цель работы — оценить, может ли ветланд один снизить фосфор до порога гипертрофии. Мы проанализировали опубликованные данные 80 проб.
Фосфор во влажный сезон превышал 0,4 мг/л во всех точках; при удалении 46 % индекс снизится с 90,5 до 81,7.
Вывод: ветланд необходим, но недостаточен.
"""

THESES_BAD = """К вопросу о состоянии водоёмов
В данной работе рассматриваются вопросы состояния водоёмов и их значение для общества.
"""


class GenreTests(unittest.TestCase):
    def test_complete_article_is_clean(self):
        found, summary = mse_genre.check(ARTICLE.splitlines(), "article")
        self.assertEqual(found, [], found)
        self.assertEqual(summary["keywords_counts"], [4])

    def test_missing_gap_and_discussion_moves(self):
        text = ARTICLE.replace("Однако эффект сочетания мер для мелких озёр тропиков не изучен. ", "")
        text = text.replace("Результат согласуется с данными [4]. Ограничение работы — отсутствие данных о составе ила. ", "")
        msgs = " ".join(m for _, m in mse_genre.check(text.splitlines(), "article")[0])
        self.assertIn("gap", msgs)
        self.assertIn("comparison", msgs)
        self.assertIn("limitations", msgs)

    def test_missing_sections_for_article(self):
        text = ARTICLE.replace("Обсуждение\n", "").replace("Материалы и методы\n", "")
        msgs = [m for _, m in mse_genre.check(text.splitlines(), "article")[0]]
        self.assertIn("no 'methods' section heading", msgs)

    def test_abstract_limits_and_keywords(self):
        long_abs = "Аннотация. В данной статье рассматриваются " + "слово " * 260
        text = ARTICLE.replace(ARTICLE.splitlines()[2], long_abs).replace("озеро; эвтрофирование; расчистка; ветланды", "озеро")
        checks = [m for c, m in mse_genre.check(text.splitlines(), "article")[0] if c == "limits"]
        self.assertTrue(any("more than 250" in m for m in checks))
        self.assertTrue(any("filler" in m for m in checks))
        self.assertTrue(any("expected 3–15" in m for m in checks))

    def test_review_needs_selection_method(self):
        msgs = " ".join(m for _, m in mse_genre.check(ARTICLE.splitlines(), "review")[0])
        self.assertIn("searched and selected", msgs)

    def test_theses(self):
        self.assertEqual(mse_genre.check(THESES_OK.splitlines(), "theses")[0], [])
        checks = {c for c, _ in mse_genre.check(THESES_BAD.splitlines(), "theses")[0]}
        self.assertEqual(checks, {"moves", "title"})

    def test_length_limits(self):
        found, _ = mse_genre.check(THESES_OK.splitlines(), "theses", max_chars=100)
        self.assertIn("length", {c for c, _ in found})
        long_theses = THESES_OK + ("Дополнительный текст без нового смысла. " * 250)
        self.assertIn("length", {c for c, _ in mse_genre.check(long_theses.splitlines(), "theses")[0]})

    def test_cli(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "a.md")
            with open(path, "w", encoding="utf-8") as f:
                f.write(ARTICLE)
            with redirect_stdout(io.StringIO()):
                self.assertEqual(mse_genre.main(["mse_genre.py", path, "--genre", "article"]), 0)
                self.assertEqual(mse_genre.main(["mse_genre.py", path, "--genre", "theses", "--max-chars", "50"]), 1)
                self.assertEqual(mse_genre.main(["mse_genre.py", path, "--genre", "novel"]), 2)


class KnownLimitFixTests(unittest.TestCase):
    """Regression tests for the blind spots listed in SKILL.md, Appendix T (v5.1 review)."""

    def test_labels_on_their_own_lines(self):
        def variant(sentences):
            return (ARTICLE.replace(ARTICLE.splitlines()[2], "Аннотация\n" + "Городское озеро сильно загрязнено. " * sentences)
                    .replace("Ключевые слова: озеро; эвтрофирование; расчистка; ветланды",
                             "Ключевые слова:\nозеро; эвтрофирование; расчистка"))
        found, summary = mse_genre.check(variant(60).splitlines(), "article")
        self.assertEqual((summary["abstract_words"], summary["keywords_counts"]), ([240], [3]))
        self.assertEqual(found, [], found)
        found, _ = mse_genre.check(variant(70).splitlines(), "article")
        self.assertTrue(any("more than 250" in m for _, m in found), found)

    def test_stock_phrase_is_not_an_implication(self):
        text = ARTICLE.replace("Следует начать с анализа ила.", "Следует отметить, что выборка мала.")
        msgs = " ".join(m for _, m in mse_genre.check(text.splitlines(), "article")[0])
        self.assertIn("implications", msgs)

    def test_section_and_figure_numbers_are_not_decimals(self):
        text = "Согласно ГОСТ Р 7.0.7-2021, §4.10, и данным рис. 1.2, табл. 2.1 и п. 3.4 значение равно 3,5 мг/л.\n"
        self.assertEqual(lint_text(text), [])
        self.assertEqual([c for c, _, _ in lint_text("Значение составило 3.5 мг/л.\n")], ["decimal"])

    def test_us_country_is_not_author_voice(self):
        text = ("Introduction\nLake monitoring in the US relies on state agencies that publish nutrient data "
                "every year, and the US network covers thousands of sites.")
        self.assertEqual(mse_style.profile(text.splitlines())["author_voice"], 0)
        text2 = text.replace("covers", "lets us compare")
        self.assertEqual(mse_style.profile(text2.splitlines())["author_voice"], 1)


ROBOTIC_V52 = """Введение
В современном мире цифровые двойники играют ключевую роль в управлении озёрами. Это не просто модель, а инструмент управления. Исследования показывают, что двойники снижают затраты. Таким образом, двойники важны для отрасли.
Не только экологи, но и экономисты проявляют интерес к двойникам водоёмов. Специалисты отмечают, что точность прогноза растёт с каждым годом. Была проведена оценка точности на трёх озёрах. Подводя итог, можно сказать, что подход перспективен.
Двойник — это не просто карта, а живая система наблюдений и расчётов. Учёные считают, что данные спутников полезны для прогноза. Осуществлён анализ ошибок модели на независимых данных. В целом, результаты подтверждают ценность подхода.
Важно подчеркнуть, что выполнена проверка модели на независимых данных за два года. Это не столько технология, сколько способ мышления о водоёме. Следовательно, внедрение необходимо во всех регионах.
"""

PLAIN_V52 = """Введение
Мы сравнили три озера, которые питаются стоками одного района. Ил с конца ледниковой эпохи в эпоху голоцена накапливал фосфор, и сегодня он отдаёт его воде каждое лето. Фосфор приходит не только со стоками, но и из ила [2], поэтому одна расчистка не помогает. Исследования показывают, что ветланды задерживают до половины фосфора [3]. Мы проверили, хватит ли этого для нашего района.
"""

ROBOTIC_EN_V52 = """Introduction
In today's fast-paced world, lake restoration is not just a technical task, but a social one. Studies show that wetlands remove phosphorus. We performed a detailed analysis of the samples. Overall, the approach is promising.
It's not about the data, it's about the decisions we make with it. Experts agree that monitoring is essential. We conducted an assessment of three lakes. Ultimately, restoration requires cooperation.
Restoration is not only ecological but also economic. We carried out a comparison of costs (Smith et al. 2020 report similar values). Studies show that costs fall over time [4]. In summary, early action pays off.
"""


class VoiceV52Tests(unittest.TestCase):
    """Template markers added in v5.2 (references/voice.md)."""

    def checks(self, text):
        p = mse_style.profile(text.splitlines())
        return p, {c for c, _ in mse_style.flags(p)}

    def test_russian_template_patterns(self):
        p, checks = self.checks(ROBOTIC_V52)
        self.assertTrue({"frames", "tails", "attribution", "verbs", "stock"} <= checks, checks)
        self.assertEqual(len(p["contrast_frames"]), 4)  # one frame matched by two patterns counts once
        self.assertEqual(p["summary_tails"], 4)
        self.assertEqual(len(p["vague_attributions"]), 3)
        self.assertEqual(len(p["split_predicates"]), 3)

    def test_plain_text_with_citations_is_not_flagged(self):
        p, checks = self.checks(PLAIN_V52)
        self.assertFalse({"frames", "tails", "attribution", "verbs", "stock"} & checks, checks)
        self.assertEqual(p["vague_attributions"], [])  # "Исследования показывают … [3]" has a citation
        self.assertEqual(len(p["contrast_frames"]), 1)  # one «не только…, но и» is normal Russian

    def test_english_template_patterns(self):
        p, checks = self.checks(ROBOTIC_EN_V52)
        self.assertTrue({"frames", "tails", "attribution", "verbs", "stock"} <= checks, checks)
        self.assertEqual(len(p["vague_attributions"]), 2)  # the cited "Studies show … [4]" is not counted

    def test_impersonal_register_has_no_voice_flag(self):
        text = "Введение\n" + " ".join(["Пробы воды отобраны в июле и проанализированы по стандартной методике."] * 60)
        p = mse_style.profile(text.splitlines())
        self.assertIn("voice", {c for c, _ in mse_style.flags(p)})
        self.assertNotIn("voice", {c for c, _ in mse_style.flags(p, impersonal=True)})  # ГОСТ report register

    def test_uniform_paragraphs(self):
        para = "Мы измерили фосфор в пробах воды и ила каждого озера в начале и в конце лета прошлого года."
        uniform = "Введение\n" + "\n".join([para] * 6)
        varied = "Введение\n" + "\n".join([para, para + " " + para + " " + para, para, para + " " + para, para, para])
        self.assertIn("layout", self.checks(uniform)[1])
        self.assertNotIn("layout", self.checks(varied)[1])


GRANT_OK = """Прогноз цветения цианобактерий в мелких озёрах по спутниковым данным
Цель проекта — построить и проверить прогноз цветения на 7 дней для трёх озёр. Задачи: собрать ряды данных, обучить модель, проверить её на 2027 году.
Актуальность. Цветение закрывает водозаборы, а прогнозов для мелких озёр нет.
Новизна: для этих озёр мы объединим спутниковые и наземные данные; поиск по Scopus в 2026 году аналогов не нашёл.
Методы: ассимиляция данных, проверка против нулевой модели.
Риски и альтернативы: облачность закрывает снимки; запасной путь — данные датчиков.
План работ: этап 1 — 2027 год, этап 2 — 2028 год.
Ожидаемые результаты: прогноз с ошибкой не более 20 %, показатель — доля верных тревог.
"""

GRANT_BAD = """Революционный подход к экологии озёр
Наш уникальный проект не имеет аналогов в мире и станет настоящим прорывом в науке. Мы изучим озёра и улучшим их состояние.
"""

REPORT_OK = """ОТЧЁТ О НАУЧНО-ИССЛЕДОВАТЕЛЬСКОЙ РАБОТЕ
РЕФЕРАТ
Отчёт 45 с., 6 рис., 3 табл., 28 источн., 2 прил.
ОЗЕРО, ФОСФОР, ЦВЕТЕНИЕ, ПРОГНОЗ, СПУТНИКОВЫЕ ДАННЫЕ
Объект исследования — мелкие озёра. Цель работы — прогноз цветения. Методы — ассимиляция данных. Результаты: ошибка прогноза 18 %.
СОДЕРЖАНИЕ
Введение 4
ВВЕДЕНИЕ
Работа выполнена по договору.
ЗАКЛЮЧЕНИЕ
Задачи решены полностью.
СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ
1. Источник.
"""

POPSCI_BAD = """Учёные доказали: кофе защищает от болезни
Сенсация! Исследование показало, что кофе связан с меньшим риском болезни. Опыты на мышах показали, что кофе защищает людей от старения.
"""

POPSCI_OK = """Чашка кофе в день и память: что показало новое исследование
Исследователи наблюдали за 2000 людьми десять лет. У тех, кто пил кофе, память ухудшалась медленнее. Это связь, а не доказанная причина: часть различий может объясняться образом жизни. Пока неизвестно, будет ли тот же эффект у тех, кто начнёт пить кофе специально. Статья опубликована в журнале в 2025 году.
"""


class AppliedGenreTests(unittest.TestCase):
    """Genres added in v5.2 (references/genres-applied.md)."""

    def checks(self, text, genre):
        found, _ = mse_genre.check(text.splitlines(), genre)
        return found

    def test_grant(self):
        self.assertEqual(self.checks(GRANT_OK, "grant"), [])
        found = self.checks(GRANT_BAD, "grant")
        labels = " ".join(m for _, m in found)
        for missing in ("aims", "risks", "work plan", "expected results"):
            self.assertIn(missing, labels)
        self.assertIn("прорывом в науке", labels)

    def test_report_gost_7_32(self):
        self.assertEqual(self.checks(REPORT_OK, "report"), [])
        bad = REPORT_OK.replace("Отчёт 45 с., 6 рис., 3 табл., 28 источн., 2 прил.\n", "").replace(
            "ОЗЕРО, ФОСФОР, ЦВЕТЕНИЕ, ПРОГНОЗ, СПУТНИКОВЫЕ ДАННЫЕ", "ОЗЕРО, ФОСФОР").replace("ЗАКЛЮЧЕНИЕ\n", "")
        labels = " ".join(m for _, m in self.checks(bad, "report"))
        self.assertIn("volume", labels)
        self.assertIn("2 keywords", labels)
        self.assertIn("ЗАКЛЮЧЕНИЕ", labels)
        long_ref = REPORT_OK.replace("Результаты: ошибка прогноза 18 %.", "Результаты: ошибка прогноза 18 %. " * 120)
        self.assertIn("850", " ".join(m for _, m in self.checks(long_ref, "report")))

    def test_popsci(self):
        self.assertEqual(self.checks(POPSCI_OK, "popsci"), [])
        checks = {c for c, _ in self.checks(POPSCI_BAD, "popsci")}
        self.assertEqual(checks, {"source", "uncertainty", "claims"})
        labels = " ".join(m for _, m in self.checks(POPSCI_BAD, "popsci"))
        self.assertIn("animal", labels)
        self.assertIn("association", labels)

    def test_breakthrough_infection_is_not_hype(self):
        text = "Breakthrough infections after vaccination\nWe aim to test whether antibodies fall; methods: we measured 200 sera."
        self.assertFalse(any(c == "claims" for c, _ in self.checks(text, "theses")))



class PilotFixesTests(unittest.TestCase):
    """Fixes from the first run on the author's own manuscripts (v5.2, 17 November 2026); synthetic fixtures only."""

    def test_numbered_heading_with_subtitle_is_recognised(self):
        self.assertEqual(mse_genre.classify_heading("1. Введение: постановка задачи"), "introduction")
        self.assertEqual(mse_genre.classify_heading("8. Выводы и заключение"), "conclusions")
        self.assertEqual(mse_genre.classify_heading("II. Methods — field sampling"), "methods")
        self.assertIsNone(mse_genre.classify_heading("1. Паспорт объекта: границы и пороги"))

    def test_overclaims_are_flagged_but_negations_are_not(self):
        for s in ("Модель доказывает, что меры эффективны.", "Схема гарантирует урожай.",
                  "Метод отличается исключительной точностью измерений.", "Схема сводит риск потерь к нулю.",
                  "The model proves that dredging works.", "It guarantees yield."):
            self.assertTrue(mse_genre.HYPE.search(s), s)
        for s in ("Это не доказывает, что меры эффективны.", "Схема не гарантирует урожай.", "исключительно в сухой сезон",
                  "This does not prove that dredging works.", "It cannot guarantee yield."):
            self.assertFalse(mse_genre.HYPE.search(s), s)

    def test_topic_first_openers_are_not_flagged(self):
        sents = ["В сухой сезон {} доля фосфора в воде росла заметно.", "Для каждого бассейна {} мы взяли пробы воды и ила.",
                 "При высокой температуре {} концентрация кислорода падала быстро."]
        text = "Введение\n" + " ".join(s.format(k) for k in range(5) for s in sents)
        self.assertNotIn("openers", {c for c, _ in mse_style.flags(mse_style.profile(text.splitlines()))})
        text2 = "Введение\n" + " ".join(f"Также озеро {k} получало стоки с полей и улиц." for k in range(5))
        self.assertIn("openers", {c for c, _ in mse_style.flags(mse_style.profile(text2.splitlines()))})

    def test_one_stock_word_in_a_long_text_is_not_flagged(self):
        para = "Мы отобрали пробы воды в четырёх бассейнах озера и измерили фосфор, азот и прозрачность в оба сезона."
        text = "Введение\n" + " ".join([para] * 30) + " Этот обзор не является систематическим."
        p = mse_style.profile(text.splitlines())
        self.assertEqual(len(p["stock_phrases"]), 1)
        self.assertNotIn("stock", {c for c, _ in mse_style.flags(p)})

    def test_glosses_and_figure_references_are_not_glue(self):
        para = ("Цифровой двойник (ЦД) озера (рис. 1) использует индекс загрязнения (WPI) и индекс трофности (TSI), "
                "а порог устойчивости (tipping point) задаёт сценарии (табл. 2) для каждого бассейна.")
        p = mse_style.profile(("Введение\n" + " ".join([para] * 8)).splitlines())
        self.assertEqual(p["parentheses_per_1000"], 0.0)
        glued = ("Мы взяли пробы (80 проб в четырёх бассейнах за два сезона) и измерили фосфор "
                 "(общий и растворённый, по стандартной методике) в каждой точке.")
        self.assertIn("glue", {c for c, _ in mse_style.flags(mse_style.profile(("Введение\n" + " ".join([glued] * 8)).splitlines()))})

    def test_udc_line_is_not_prose(self):
        text = ("УДК 504.455 МАТЕРИАЛЫ НАУЧНОЙ КОНФЕРЕНЦИИ О ВОДНЫХ ЭКОСИСТЕМАХ И УПРАВЛЕНИИ ПРИРОДНЫМИ РЕСУРСАМИ РЕГИОНА\n"
                "Введение\nМы измерили фосфор в пробах воды и ила каждого озера в начале и в конце лета прошлого года.")
        self.assertNotIn("удк", dict(mse_style.profile(text.splitlines())["top_openers"]))

    def test_incomplete_reference_record_is_flagged(self):
        text = ("Фосфор накапливается в иле [1], а стоки его пополняют [2].\n\nСписок источников\n\n"
                "1. Иванов И.И. Фосфор в озёрах // Водные ресурсы. 2020.\n"
                "2. Petrov P. Lake loads // Water. 2021. Vol. 3. P. 10–20. URL: https://example.org/a (дата обращения: 01.11.2026).\n")
        records = [m for c, _, m in lint_text(text) if c == "record"]
        self.assertEqual(len(records), 1)
        self.assertIn("reference 1", records[0])

    def test_url_slashes_are_not_a_record_separator(self):
        text = ("Технология описана в патенте [1].\n\nСписок источников\n\n"
                "1. Пат. 123 Япония. Способ обработки ила. URL: https://patents.example.org/p/123 (дата обращения: 12.10.2026).\n")
        self.assertEqual([c for c, _, _ in lint_text(text)], [])


JA_BAD = """はじめに
本研究では湖の底泥をを分析した。試料は２０２５年に採取しました。濃度は1.2 mg/Lであった。リンの濃度は高いです。この方法で濃度を測定することができる。調査を実施した結果、溶出が多いということになる。
夜間でも試料は見れる。影響がないわけではない．
湖沼の底泥に含まれる有機物と栄養塩類の量は季節によって大きく変動し、特に夏季には水温の上昇に伴って微生物の分解活動が活発になるため、底泥からのリンの溶出量が増加し、結果として湖水中の栄養塩濃度が高まり、植物プランクトンの増殖が促進されると考えられる。
"""

JA_OK = """湖沼底泥からのリン溶出に及ぼす水温の影響
要旨：本研究では、底泥からのリン溶出に水温が与える影響を室内実験で調べた。溶出速度は水温とともに増加した。
キーワード：底泥、リン、溶出、水温
1．はじめに
浅い湖では底泥からのリン溶出が水質に大きく影響する[1]。しかし、水温の影響は十分に明らかになっていない[2]。本研究の目的は、水温と溶出速度の関係を明らかにすることである。
2．材料と方法
2025年8月に柱状試料を3本採取し、15、20、25℃で14日間培養した。試料を見れば違いは明らかであったものの、測定値で比較した。
3．結果
溶出速度は15℃で1.2、25℃で3.4 mg/m2/dであった。
4．考察
この結果は既往の報告[3]と一致する。ただし、試料は1地点に限られ、一般化には限界がある。今後は複数地点で検証する必要がある。
5．結論
水温の上昇は底泥からのリン溶出を促進する。
参考文献
[1] 著者A. 題名. 雑誌名. 2020, vol. 1, p. 1-10.
[2] 著者B. 題名. 雑誌名. 2021, vol. 2, p. 11-20.
[3] 著者C. 題名. 雑誌名. 2022, vol. 3, p. 21-30.
"""


class LanguageCheckTests(unittest.TestCase):
    """mse_grammar.py — mechanical slips in Russian, English and Japanese (v5.2); synthetic fixtures only."""

    def kinds(self, text):
        return [c for c, _, _ in mse_grammar.check(text.splitlines())]

    def test_russian_slips(self):
        text = ("Мы отобрали пробы в в четырёх бассейнах озера  и измерили фосфор ,азот и прозрачность.\n"
                "Данные нужны для сельско хозяйственных и научно исследовательских работ.\n")
        kinds = self.kinds(text)
        self.assertEqual(kinds.count("repeat"), 1)
        self.assertEqual(kinds.count("compound"), 2)
        self.assertIn("space", kinds)

    def test_clean_russian_and_english_pass(self):
        self.assertEqual(self.kinds(CLEAN), [])
        self.assertEqual(self.kinds("We know that that result had had an effect, as Smith (2020) showed.\n"), [])
        self.assertEqual(self.kinds("The the samples were taken in July.\n"), ["repeat"])
        self.assertEqual(self.kinds("Мы знаем, что что-то изменилось в составе ила за лето.\n"), [])
        self.assertFalse(mse_lint.is_japanese("PCS Co., Ltd. (株式会社ピーシーエス), Саппоро, Япония"))
        self.assertTrue(mse_lint.is_japanese("本研究ではPCS法を用いた。"))

    def test_japanese_slips(self):
        kinds = self.kinds(JA_BAD)
        for kind in ("style", "punct", "width", "particle", "ra-nuki", "negation", "wordy", "long"):
            self.assertIn(kind, kinds, kind)

    def test_clean_japanese_passes(self):
        # 「見れば」 (a conditional), 「ものの」, section numbers «1．» and the reference list are not slips
        self.assertEqual(self.kinds(JA_OK), [])

    def test_japanese_article_structure(self):
        found, summary = mse_genre.check(JA_OK.splitlines(), "article")
        self.assertEqual(found, [], found)
        self.assertTrue(str(summary["abstract_words"][0]).endswith("字"))
        self.assertIn("claims", {c for c, _ in mse_genre.check(JA_OK.replace("5．結論\n", "5．結論\nこの手法は画期的である。\n").splitlines(), "article")[0]})

    def test_japanese_reference_heading_and_style_note(self):
        lines = JA_OK.splitlines()
        self.assertEqual(lines[mse_lint.split_references(lines)], "参考文献")
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "ja.txt")
            with open(path, "w", encoding="utf-8") as f:
                f.write(JA_OK)
            out = io.StringIO()
            with redirect_stdout(out):
                code = mse_style.main(["mse_style.py", path])
            self.assertEqual(code, 0)
            self.assertIn("not applicable", out.getvalue())

    def test_grammar_cli_exit_codes(self):
        with tempfile.TemporaryDirectory() as d:
            good, bad = os.path.join(d, "good.txt"), os.path.join(d, "bad.txt")
            with open(good, "w", encoding="utf-8") as f:
                f.write(JA_OK)
            with open(bad, "w", encoding="utf-8") as f:
                f.write(JA_BAD)
            with redirect_stdout(io.StringIO()):
                self.assertEqual(mse_grammar.main(["mse_grammar.py", good]), 0)
                self.assertEqual(mse_grammar.main(["mse_grammar.py", bad]), 1)
                self.assertEqual(mse_grammar.main(["mse_grammar.py", os.path.join(d, "missing.txt")]), 2)

if __name__ == "__main__":
    unittest.main(verbosity=2)
