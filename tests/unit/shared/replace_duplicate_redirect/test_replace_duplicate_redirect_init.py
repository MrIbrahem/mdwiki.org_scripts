"""
Unit tests for flask_app/main_app/shared/replace_duplicate_redirect/__init__.py module.

"""

from flask_app.main_app.shared.replace_duplicate_redirect import (
    replace_redirect_link,
    replace_wikilink_destinations,
)

import pytest

_test_data = [
    (
        "Standard inline replacement",
        "This is a [[RedirectPage]] in a sentence.",
        "RedirectPage",
        "FinalTarget",
        "This is a [[FinalTarget]] in a sentence."
    ),
    (
        "Link with display text (piped link)",
        "We can click [[ RedirectPage |this link]] here.",
        "RedirectPage",
        "FinalTarget",
        "We can click [[FinalTarget|this link]] here."
    ),
    (
        "Multiple links, only one matches",
        "See [[RedirectPage]] but do not touch [[OtherPage]].",
        "RedirectPage",
        "FinalTarget",
        "See [[FinalTarget]] but do not touch [[OtherPage]]."
    ),
    (
        "Whitespace handling in target",
        "Link to [[ RedirectPage ]].",
        "RedirectPage",
        "FinalTarget",
        "Link to [[FinalTarget]]."
    ),
    (
        "No matching links in text",
        "This text only has [[UnrelatedPage]].",
        "RedirectPage",
        "FinalTarget",
        "This text only has [[UnrelatedPage]]."
    ),
]

@pytest.mark.parametrize(
    "description, input_text, redirect_to, final_target, expected_correct_text",
    _test_data,
    ids=lambda x: x[0]
)
def test_replace_redirect_link(description, input_text, redirect_to, final_target, expected_correct_text):
    # 1. Test the old function
    old_result = replace_redirect_link(input_text, redirect_to, final_target)

    # Assert the old function FAILS to produce the correct text
    # (It always destroys the text and returns a raw redirect string)
    assert old_result != expected_correct_text, f"Old function unexpectedly passed: {description}"
    assert old_result == f"#REDIRECT [[{final_target}]]"

@pytest.mark.parametrize(
    "description, input_text, redirect_to, final_target, expected_correct_text",
    _test_data,
    ids=lambda x: x[0]
)
def test_replace_wikilink_destinations(description, input_text, redirect_to, final_target, expected_correct_text):
    # 2. Test the new function
    new_result = replace_wikilink_destinations(input_text, redirect_to, final_target)

    # Assert the new function SUCCEEDS and matches the expected behavior
    assert new_result == expected_correct_text, f"New function failed: {description}"


class TestReplaceWikilinkDestinations:
    ...
