from apps.recipes.templatetags.cooklang_steps import cooklang_step


def test_plain_step_is_escaped():
    assert cooklang_step("Mélangez <bien> & servez") == "Mélangez &lt;bien&gt; &amp; servez"


def test_ingredient_mention_shows_display_name_without_meta():
    assert cooklang_step("Faites fondre le @Chocolat_noir{200%g}.") == (
        'Faites fondre le <strong class="step-ingredient">Chocolat noir</strong>.'
    )


def test_cookware_mention_stops_at_punctuation():
    assert cooklang_step("Préchauffez le #Four. Puis le #Moule_à_gâteau{}") == (
        'Préchauffez le <span class="step-cookware">Four</span>. '
        'Puis le <span class="step-cookware">Moule à gâteau</span>'
    )


def test_hash_followed_by_digit_stays_text():
    assert cooklang_step("Voir étape #2") == "Voir étape #2"


def test_timer_shows_quantity_and_unit():
    assert cooklang_step("Cuire ~{20%minutes}.") == 'Cuire <span class="step-timer">20 minutes</span>.'


def test_named_timer_without_quantity_falls_back_to_name():
    assert cooklang_step("Laisser ~repos_long{}") == 'Laisser <span class="step-timer">repos long</span>'


def test_mention_content_is_escaped():
    assert cooklang_step("@<b>") == '<strong class="step-ingredient">&lt;b&gt;</strong>'
