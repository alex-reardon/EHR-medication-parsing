import pytest

from rxnorm_mapping.rxnorm_mapper import (
    _clean_sbdf_to_ingredient_key,
    _normalize_input,
    _score_to_confidence,
    build_ledd_key,
    extract_formulation,
)


# ---------------------------------------------------------------------------
# _score_to_confidence
# ---------------------------------------------------------------------------

def test_confidence_high():
    assert _score_to_confidence(95) == "high"

def test_confidence_high_at_boundary():
    assert _score_to_confidence(92) == "high"

def test_confidence_medium():
    assert _score_to_confidence(88) == "medium"

def test_confidence_medium_at_boundary():
    assert _score_to_confidence(85) == "medium"

def test_confidence_low():
    assert _score_to_confidence(70) == "low"

def test_confidence_nan_is_low():
    assert _score_to_confidence(float("nan")) == "low"

def test_confidence_none_is_low():
    assert _score_to_confidence(None) == "low"


# ---------------------------------------------------------------------------
# _normalize_input  (separator whitespace bug regression)
# ---------------------------------------------------------------------------

def test_normalize_slash_with_spaces():
    # "levodopa / benserazide" must not produce triple-spaces
    result = _normalize_input("levodopa / benserazide")
    assert result == "levodopa benserazide"
    assert "  " not in result

def test_normalize_slash_no_spaces():
    assert _normalize_input("levodopa/carbidopa") == "levodopa carbidopa"

def test_normalize_plus():
    assert _normalize_input("levodopa + carbidopa") == "levodopa carbidopa"

def test_normalize_ampersand():
    assert _normalize_input("levodopa & carbidopa") == "levodopa carbidopa"

def test_normalize_no_separator():
    assert _normalize_input("levodopa") == "levodopa"

def test_normalize_multiple_separators():
    result = _normalize_input("a / b + c")
    assert result == "a b c"


# ---------------------------------------------------------------------------
# extract_formulation
# ---------------------------------------------------------------------------

def test_formulation_er():
    assert extract_formulation("sinemet ER") == "ER"

def test_formulation_er_extended_release():
    assert extract_formulation("levodopa extended-release") == "ER"

def test_formulation_cr():
    assert extract_formulation("sinemet CR") == "CR"

def test_formulation_sr():
    assert extract_formulation("levodopa SR") == "SR"

def test_formulation_patch():
    assert extract_formulation("rotigotine transdermal") == "patch"

def test_formulation_patch_word():
    assert extract_formulation("neupro patch") == "patch"

def test_formulation_odt():
    assert extract_formulation("selegiline ODT") == "ODT"

def test_formulation_injectable():
    assert extract_formulation("apomorphine injection") == "injectable"

def test_formulation_none():
    assert extract_formulation("levodopa") is None

def test_formulation_case_insensitive():
    assert extract_formulation("Sinemet er") == "ER"


# ---------------------------------------------------------------------------
# _clean_sbdf_to_ingredient_key
# ---------------------------------------------------------------------------

def test_clean_sbdf_strips_dose_form_words():
    result = _clean_sbdf_to_ingredient_key("carbidopa / levodopa oral tablet")
    assert "oral" not in result
    assert "tablet" not in result

def test_clean_sbdf_strips_brackets():
    result = _clean_sbdf_to_ingredient_key(
        "carbidopa / levodopa oral tablet [sinemet cr]"
    )
    assert "sinemet" not in result

def test_clean_sbdf_strips_extended_release():
    result = _clean_sbdf_to_ingredient_key(
        "carbidopa / levodopa extended release oral tablet"
    )
    assert "extended" not in result
    assert "release" not in result

def test_clean_sbdf_sorts_ingredients_consistently():
    r1 = _clean_sbdf_to_ingredient_key("levodopa / carbidopa oral tablet")
    r2 = _clean_sbdf_to_ingredient_key("carbidopa / levodopa oral tablet")
    assert r1 == r2

def test_clean_sbdf_retains_ingredients():
    result = _clean_sbdf_to_ingredient_key("carbidopa / levodopa oral tablet")
    assert "carbidopa" in result
    assert "levodopa" in result


# ---------------------------------------------------------------------------
# build_ledd_key
# ---------------------------------------------------------------------------

def test_ledd_key_with_formulation():
    assert build_ledd_key("carbidopa / levodopa", "ER") == "carbidopa/levodopa_ER"

def test_ledd_key_no_formulation_defaults_ir():
    assert build_ledd_key("levodopa", None) == "levodopa_IR"

def test_ledd_key_none_canonical_returns_none():
    assert build_ledd_key(None, "ER") is None

def test_ledd_key_spaces_replaced():
    key = build_ledd_key("carbidopa / levodopa", "CR")
    assert " " not in key
