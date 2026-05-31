"""
Unit tests for flask_app/main_app/shared/replace_wikilink/__init__.py module.

"""

import pytest
from flask_app.main_app.shared.replace_wikilink import replace_wikilink_destinations

_test_data = [
    (
        "Standard inline replacement",
        "This is a [[RedirectPage]] in a sentence.",
        "RedirectPage",
        "FinalTarget",
        "This is a [[FinalTarget]] in a sentence.",
    ),
    (
        "Link with display text (piped link)",
        "We can click [[ RedirectPage |this link]] here.",
        "RedirectPage",
        "FinalTarget",
        "We can click [[FinalTarget|this link]] here.",
    ),
    (
        "Multiple links, only one matches",
        "See [[RedirectPage]] but do not touch [[OtherPage]].",
        "RedirectPage",
        "FinalTarget",
        "See [[FinalTarget]] but do not touch [[OtherPage]].",
    ),
    (
        "Whitespace handling in target",
        "Link to [[ RedirectPage ]].",
        "RedirectPage",
        "FinalTarget",
        "Link to [[FinalTarget]].",
    ),
    (
        "No matching links in text",
        "This text only has [[UnrelatedPage]].",
        "RedirectPage",
        "FinalTarget",
        "This text only has [[UnrelatedPage]].",
    ),
]


@pytest.mark.parametrize(
    "description, input_text, redirect_to, final_target, expected_correct_text", _test_data, ids=lambda x: x[0]
)
def test_replace_wikilink_destinations(description, input_text, redirect_to, final_target, expected_correct_text):
    # 2. Test the new function
    new_result = replace_wikilink_destinations(input_text, redirect_to, final_target)

    # Assert the new function SUCCEEDS and matches the expected behavior
    assert new_result == expected_correct_text, f"New function failed: {description}"


class TestReplaceWikilinkDestinations:

    def test_underscore_in_text_space_in_target(self):
        # Test converting an underscore in the source text to a space in the target
        input_text = "هذا رابط إلى [[الصفحة_الرئيسية]] هنا."
        redirect_to = "الصفحة الرئيسية"
        final_target = "الواجهة"
        expected_text = "هذا رابط إلى [[الواجهة]] هنا."

        result = replace_wikilink_destinations(input_text, redirect_to, final_target)

        assert result == expected_text

    def test_space_in_text_underscore_in_target(self):
        # Test matching a space in the source text against an underscore in the target
        input_text = "نص يحتوي على [[New York City]]."
        redirect_to = "New_York_City"
        final_target = "NYC"
        expected_text = "نص يحتوي على [[NYC]]."

        result = replace_wikilink_destinations(input_text, redirect_to, final_target)

        assert result == expected_text

    def test_ignore_first_letter_capitalization(self):
        # MediaWiki links are case-insensitive for the first letter
        input_text = "انظر إلى [[wikipedia]]."
        redirect_to = "Wikipedia"
        final_target = "Wikimedia"
        expected_text = "انظر إلى [[Wikimedia]]."

        result = replace_wikilink_destinations(input_text, redirect_to, final_target)

        assert result == expected_text

    def test_preserve_url_fragment(self):
        # The #fragment should be kept and appended to the new target
        input_text = "اقرأ في [[تاريخ#العصر الحديث|التاريخ المعاصر]]."
        redirect_to = "تاريخ"
        final_target = "تاريخ العالم"
        expected_text = "اقرأ في [[تاريخ العالم#العصر الحديث|التاريخ المعاصر]]."

        result = replace_wikilink_destinations(input_text, redirect_to, final_target)

        assert result == expected_text

    def test_irregular_whitespace(self):
        # Extra spaces around the link target should be normalized
        input_text = "نص [[  مصر  ]] قديم."
        redirect_to = "مصر"
        final_target = "جمهورية مصر العربية"
        expected_text = "نص [[جمهورية مصر العربية]] قديم."

        result = replace_wikilink_destinations(input_text, redirect_to, final_target)

        assert result == expected_text

    def test_arabic_language_with_piped_link(self):
        # Ensure non-Latin characters and piped (display) text work correctly
        input_text = "مرحبا بك في [[ويكيبيديا العربية|الموسوعة الحرة]]."
        redirect_to = "ويكيبيديا العربية"
        final_target = "ويكيبيديا"
        expected_text = "مرحبا بك في [[ويكيبيديا|الموسوعة الحرة]]."

        result = replace_wikilink_destinations(input_text, redirect_to, final_target)

        assert result == expected_text

    def test_russian_language(self):
        # Test with Cyrillic characters
        input_text = "Текст с [[Россия]]."
        redirect_to = "Россия"
        final_target = "Российская Федерация"
        expected_text = "Текст с [[Российская Федерация]]."

        result = replace_wikilink_destinations(input_text, redirect_to, final_target)

        assert result == expected_text

    def test_category_namespace(self):
        # Test links that include MediaWiki namespaces
        input_text = "أضف إلى [[تصنيف:أشخاص_من_مصر]]."
        redirect_to = "تصنيف:أشخاص من مصر"
        final_target = "تصنيف:مصريون"
        expected_text = "أضف إلى [[تصنيف:مصريون]]."

        result = replace_wikilink_destinations(input_text, redirect_to, final_target)

        assert result == expected_text
