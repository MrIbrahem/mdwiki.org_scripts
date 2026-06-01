""" """

from pathlib import Path

from flask_app.main_app.shared.new_updater import med_updater_one


def test_1():

    Dir = Path(__file__).parent

    text_file = Dir / "texts/test1/work_on_text_source.wiki"
    expected_file = Dir / "texts/test1/work_on_text_expected.wiki"

    text = text_file.read_text(encoding="utf-8")
    expected = expected_file.read_text(encoding="utf-8")

    newtext = med_updater_one("test", text)

    with open(Dir / "texts/test1/work_on_text_result.wiki", "w", encoding="utf-8") as f:
        f.write(newtext)

    assert newtext.strip() == expected.strip()


def test_2():

    Dir = Path(__file__).parent

    text_file = Dir / "texts/test2/work_on_text_source.wiki"
    expected_file = Dir / "texts/test2/work_on_text_expected.wiki"

    text = text_file.read_text(encoding="utf-8")
    expected = expected_file.read_text(encoding="utf-8")

    newtext = med_updater_one("test", text)

    with open(Dir / "texts/test2/work_on_text_result.wiki", "w", encoding="utf-8") as f:
        f.write(newtext)

    assert newtext.strip() == expected.strip()


def test_3():

    Dir = Path(__file__).parent

    text_file = Dir / "texts/test3/work_on_text_source.wiki"
    expected_file = Dir / "texts/test3/work_on_text_expected.wiki"

    text = text_file.read_text(encoding="utf-8")
    expected = expected_file.read_text(encoding="utf-8")

    newtext = med_updater_one("test", text)

    with open(Dir / "texts/test3/work_on_text_result.wiki", "w", encoding="utf-8") as f:
        f.write(newtext)

    assert newtext.strip() == expected.strip()
