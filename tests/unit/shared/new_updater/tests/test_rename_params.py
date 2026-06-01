""" """

from flask_app.main_app.shared.new_updater.bots.old_params import rename_params

old = """{{drugbox
|side effects=test
<!-- asdadsxxx -->

|temp = {{sub
|side effects=test1<!-- asdads -->
}}
}}
{{infobox drug
|side effects=22
|side effects=211
}}"""

expected = """{{drugbox
|side_effects=test
<!-- asdadsxxx -->

|temp = {{sub
|side effects=test1<!-- asdads -->
}}
}}
{{infobox drug
|side_effects=211
}}"""


def test_it():
    new_text = rename_params(old)

    assert new_text == expected
