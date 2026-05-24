
from python.fixref.fixref_text_new import fix_ref_template


def test_fix_ref_template():
    old = """{{استشهاد ويب|url=https://www.volksgezondheidenzorg.info/sites/default/files/map/detail_data/klik_corona04032020.csv|title=Aantal Coronavirus (COVID-19)-meldingen. Per gemeente (waar de patiënt woont), peildatum 4 maart 2020|date=4 March 2020|website=volksgezondheidenzorg.info|language=nl|format=CSV|archive-url=https://web.archive.org/web/20200308095940/https://www.volksgezondheidenzorg.info/sites/default/files/map/detail_data/klik_corona04032020.csv|archive-date=8 March 2020|access-date=6 March 2020|layurl=https://www.volksgezondheidenzorg.info/onderwerp/infectieziekten/regionaal-internationaal/coronavirus-covid-19}}"""

    new = fix_ref_template(old)
    assert new != old
