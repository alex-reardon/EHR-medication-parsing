import pandas as pd
import pytest

from rxnorm_mapping.reorder_dose import (
    _fuzzy_token_match,
    _get_reorder_index,
    _order_flipped,
    _reorder_dose_for_swap,
    _tokens,
    apply_reorder_dose,
)


# ---------------------------------------------------------------------------
# _tokens
# ---------------------------------------------------------------------------

def test_tokens_basic():
    assert _tokens("levodopa/carbidopa") == ["levodopa", "carbidopa"]

def test_tokens_lowercases():
    assert _tokens("Levodopa") == ["levodopa"]

def test_tokens_strips_numbers_and_punctuation():
    result = _tokens("levodopa 25mg")
    assert "levodopa" in result
    assert "25" not in result

def test_tokens_empty_string():
    assert _tokens("") == []


# ---------------------------------------------------------------------------
# _fuzzy_token_match
# ---------------------------------------------------------------------------

def test_fuzzy_token_match_exact():
    result = _fuzzy_token_match(["levodopa", "carbidopa"], ["levodopa", "carbidopa"])
    assert result == {"levodopa": "levodopa", "carbidopa": "carbidopa"}

def test_fuzzy_token_match_misspelling():
    result = _fuzzy_token_match(["levidopa", "carbidopa"], ["levodopa", "carbidopa"])
    assert "levodopa" in result
    assert "carbidopa" in result

def test_fuzzy_token_match_below_threshold():
    result = _fuzzy_token_match(["aspirin"], ["levodopa"], threshold=80)
    assert result == {}

def test_fuzzy_token_match_no_reuse():
    # the same input token shouldn't be matched twice
    result = _fuzzy_token_match(["levodopa"], ["levodopa", "levodopa"])
    assert len(result) == 1


# ---------------------------------------------------------------------------
# _order_flipped
# ---------------------------------------------------------------------------

def test_order_flipped_same_order():
    assert _order_flipped("carbidopa/levodopa", "carbidopa / levodopa") is False

def test_order_flipped_different_order():
    assert _order_flipped("levodopa/carbidopa", "carbidopa / levodopa") is True

def test_order_flipped_nan_matched():
    assert _order_flipped("levodopa", float("nan")) is False

def test_order_flipped_none_matched():
    assert _order_flipped("levodopa", None) is False

def test_order_flipped_single_ingredient():
    assert _order_flipped("levodopa", "levodopa") is False

def test_order_flipped_list_input():
    assert _order_flipped(["levodopa", "carbidopa"], "carbidopa / levodopa") is True

def test_order_flipped_misspelled_input():
    assert _order_flipped("levidopa/carbidopa", "carbidopa / levodopa") is True

def test_order_flipped_three_ingredients():
    assert _order_flipped(
        "levodopa/carbidopa/entacapone",
        "carbidopa / entacapone / levodopa",
    ) is True


# ---------------------------------------------------------------------------
# _get_reorder_index
# ---------------------------------------------------------------------------

def test_get_reorder_index_swap():
    assert _get_reorder_index("levodopa/carbidopa", "carbidopa / levodopa") == [1, 0]

def test_get_reorder_index_already_correct():
    assert _get_reorder_index("carbidopa/levodopa", "carbidopa / levodopa") == [0, 1]

def test_get_reorder_index_three_ingredients():
    result = _get_reorder_index(
        "levodopa/carbidopa/entacapone",
        "carbidopa / entacapone / levodopa",
    )
    assert result == [1, 2, 0]

def test_get_reorder_index_token_count_mismatch():
    assert _get_reorder_index("levodopa", "carbidopa / levodopa") is None

def test_get_reorder_index_no_confident_match():
    assert _get_reorder_index("aspirin", "levodopa") is None


# ---------------------------------------------------------------------------
# _reorder_dose_for_swap
# ---------------------------------------------------------------------------

def test_reorder_dose_format_a_swap():
    assert _reorder_dose_for_swap([25, 100], [1, 0]) == [100, 25]

def test_reorder_dose_format_a_three():
    assert _reorder_dose_for_swap([150, 37.5, 200], [1, 2, 0]) == [37.5, 200, 150]

def test_reorder_dose_format_a_legacy_fallback():
    assert _reorder_dose_for_swap([25, 100]) == [100, 25]

def test_reorder_dose_format_b_slash_string():
    assert _reorder_dose_for_swap(["25/100"], [1, 0]) == ["100/25"]

def test_reorder_dose_format_b_with_unit():
    assert _reorder_dose_for_swap(["25/100 mg"], [1, 0]) == ["100/25 mg"]

def test_reorder_dose_format_b_three_values():
    assert _reorder_dose_for_swap(["100/25/200"], [1, 2, 0]) == ["25/200/100"]

def test_reorder_dose_single_value_unchanged():
    assert _reorder_dose_for_swap(["100"]) == ["100"]

def test_reorder_dose_empty_list():
    assert _reorder_dose_for_swap([]) == []

def test_reorder_dose_not_a_list_passthrough():
    assert _reorder_dose_for_swap("100") == "100"

def test_reorder_dose_index_order_none_three_items_unchanged():
    # can't safely reorder 3 items without explicit index_order
    assert _reorder_dose_for_swap([10, 20, 30]) == [10, 20, 30]


# ---------------------------------------------------------------------------
# apply_reorder_dose (integration)
# ---------------------------------------------------------------------------

def _make_df(parsed, match, dose):
    return pd.DataFrame({
        "parsed": [parsed],
        "best_rxnorm_match": [match],
        "dose": [dose],
    })

def test_apply_reorder_dose_flipped():
    df = _make_df("levodopa/carbidopa", "carbidopa / levodopa", [25, 100])
    result = apply_reorder_dose(df, input_col="parsed", match_col="best_rxnorm_match")
    assert result["token_order_flipped"].iloc[0] == True
    assert result["dose_reordered"].iloc[0] == [100, 25]

def test_apply_reorder_dose_not_flipped():
    df = _make_df("carbidopa/levodopa", "carbidopa / levodopa", [25, 100])
    result = apply_reorder_dose(df, input_col="parsed", match_col="best_rxnorm_match")
    assert result["token_order_flipped"].iloc[0] == False
    assert result["dose_reordered"].iloc[0] == [25, 100]

def test_apply_reorder_dose_no_match():
    df = _make_df("levodopa", float("nan"), ["100 mg"])
    result = apply_reorder_dose(df, input_col="parsed", match_col="best_rxnorm_match")
    assert result["token_order_flipped"].iloc[0] == False

def test_apply_reorder_dose_does_not_mutate_input():
    df = _make_df("levodopa/carbidopa", "carbidopa / levodopa", [25, 100])
    original = df.copy()
    apply_reorder_dose(df, input_col="parsed", match_col="best_rxnorm_match")
    pd.testing.assert_frame_equal(df, original)

def test_apply_reorder_dose_stringified_dose():
    # dose col may arrive as a string when loaded from CSV
    df = _make_df("levodopa/carbidopa", "carbidopa / levodopa", "[25, 100]")
    result = apply_reorder_dose(df, input_col="parsed", match_col="best_rxnorm_match")
    assert result["dose_reordered"].iloc[0] == [100, 25]
