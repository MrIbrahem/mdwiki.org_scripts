""" """

from pathlib import Path

from flask_app.main_app.shared.new_updater import FixChembox


def test_1():

    Dir = Path(__file__).parent

    text_file = Dir / "texts/chembox/work_on_text_source.wiki"
    expected_file = Dir / "texts/chembox/work_on_text_expected.wiki"

    text = text_file.read_text(encoding="utf-8")
    expected = expected_file.read_text(encoding="utf-8")

    bot = FixChembox(text)

    newtext = bot.run()

    with open(Dir / "texts/chembox/work_on_text_result.wiki", "w", encoding="utf-8") as f:
        f.write(newtext)

    assert newtext.strip() == expected.strip()
