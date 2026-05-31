""" """

from flask_app.main_app.shared.new_updater import MoveExternalLinksSection

text = """"""

expected = """"""


def test_it():

    bot = MoveExternalLinksSection(str(text))

    new_text = bot.make_new_txt()

    assert new_text == expected
