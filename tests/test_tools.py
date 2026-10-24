#!/usr/bin/env python3
"""Unit tests for mse_lint.py and mse_diff.py (standard library only).

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


if __name__ == "__main__":
    unittest.main(verbosity=2)
