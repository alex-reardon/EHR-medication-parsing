import pandas as pd
import pytest

from rxnorm_mapping.rxnorm_selector import apply_rxnorm_selector


def _make_df(
    score_p=None, tty_p=None, rxnorm_match_p=None, rxcui_p=None, sbdf_p=None, pc_p=None,
    score_c=None, tty_c=None, rxnorm_match_c=None, rxcui_c=None, sbdf_c=None, pc_c=None,
    clean_text="levodopa", parenthetical_text=None,
):
    return pd.DataFrame([{
        "rxnorm_match_parenthetical_text":  rxnorm_match_p,
        "rxcui_parenthetical_text":         rxcui_p,
        "score_parenthetical_text":         score_p,
        "tty_parenthetical_text":           tty_p,
        "sbdf_parenthetical_text":          sbdf_p,
        "parse_confidence_parenthetical_text": pc_p,
        "rxnorm_match_clean_text":          rxnorm_match_c,
        "rxcui_clean_text":                 rxcui_c,
        "score_clean_text":                 score_c,
        "tty_clean_text":                   tty_c,
        "sbdf_clean_text":                  sbdf_c,
        "parse_confidence_clean_text":      pc_c,
        "clean_text":                       clean_text,
        "parenthetical_text":               parenthetical_text,
    }])


# ---------------------------------------------------------------------------
# Winner selection
# ---------------------------------------------------------------------------

def test_clean_wins_on_higher_score():
    df = _make_df(
        score_p=88, tty_p="IN",
        score_c=95, tty_c="IN",
        rxnorm_match_c="levodopa", clean_text="levodopa",
    )
    result = apply_rxnorm_selector(df, suffix_parenthetical_text="_parenthetical_text", suffix_clean_text="_clean_text")
    assert result["best_score"].iloc[0] == 95
    assert result["parsed"].iloc[0] == "levodopa"

def test_parenthetical_wins_on_higher_score():
    df = _make_df(
        score_p=96, tty_p="IN", rxnorm_match_p="sinemet",
        score_c=88, tty_c="IN",
        parenthetical_text="sinemet",
    )
    result = apply_rxnorm_selector(df, suffix_parenthetical_text="_parenthetical_text", suffix_clean_text="_clean_text")
    assert result["best_score"].iloc[0] == 96
    assert result["parsed"].iloc[0] == "sinemet"

def test_bn_beats_in_at_equal_score():
    # BN priority=0 should beat IN priority=2
    df = _make_df(
        score_p=90, tty_p="BN", rxnorm_match_p="sinemet",
        score_c=90, tty_c="IN", rxnorm_match_c="levodopa",
        clean_text="levodopa", parenthetical_text="sinemet",
    )
    result = apply_rxnorm_selector(df, suffix_parenthetical_text="_parenthetical_text", suffix_clean_text="_clean_text")
    assert result["best_rxnorm_match"].iloc[0] == "sinemet"
    assert result["parsed"].iloc[0] == "sinemet"

def test_min_beats_in_at_equal_score():
    df = _make_df(
        score_p=90, tty_p="MIN", rxnorm_match_p="carbidopa / levodopa",
        score_c=90, tty_c="IN",  rxnorm_match_c="levodopa",
        clean_text="levodopa", parenthetical_text="carbidopa / levodopa",
    )
    result = apply_rxnorm_selector(df, suffix_parenthetical_text="_parenthetical_text", suffix_clean_text="_clean_text")
    assert result["best_rxnorm_match"].iloc[0] == "carbidopa / levodopa"

def test_fallback_to_clean_when_both_missing():
    df = _make_df(clean_text="levodopa")
    result = apply_rxnorm_selector(df, suffix_parenthetical_text="_parenthetical_text", suffix_clean_text="_clean_text")
    assert result["parsed"].iloc[0] == "levodopa"


# ---------------------------------------------------------------------------
# Output columns
# ---------------------------------------------------------------------------

def test_best_parse_confidence_returned():
    df = _make_df(
        score_c=95, tty_c="IN", pc_c="high",
        clean_text="levodopa",
    )
    result = apply_rxnorm_selector(df, suffix_parenthetical_text="_parenthetical_text", suffix_clean_text="_clean_text")
    assert result["best_parse_confidence"].iloc[0] == "high"

def test_all_expected_columns_present():
    df = _make_df(clean_text="levodopa")
    result = apply_rxnorm_selector(df, suffix_parenthetical_text="_parenthetical_text", suffix_clean_text="_clean_text")
    for col in ("best_rxnorm_match", "best_rxcui", "best_score", "best_parse_confidence", "parsed"):
        assert col in result.columns

def test_output_columns_added():
    df = _make_df(score_c=90, tty_c="IN", clean_text="levodopa")
    result = apply_rxnorm_selector(df, suffix_parenthetical_text="_parenthetical_text", suffix_clean_text="_clean_text")
    for col in ("best_rxnorm_match", "best_rxcui", "best_score", "best_parse_confidence", "parsed"):
        assert col in result.columns
