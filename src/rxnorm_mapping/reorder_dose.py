from __future__ import annotations
import ast
import logging
import re

import pandas as pd
from rapidfuzz import fuzz

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Shared helpers
# ─────────────────────────────────────────────────────────────────────────────

def _tokens(text: str) -> list[str]:
    """Extract alphabetic tokens from a string, lowercased."""
    return re.findall(r'[a-z]+', text.lower())


def _fuzzy_token_match(
    input_tokens: list[str],
    ref_tokens: list[str],
    threshold: int = 80,
) -> dict[str, str]:
    """
    Map each ref_token to its best-matching input_token above threshold.
    Returns {ref_token: input_token} for matched pairs.
    """
    mapping: dict[str, str] = {}
    used: set[str] = set()
    for ref in ref_tokens:
        best_tok, best_score = None, 0
        for inp in input_tokens:
            if inp in used:
                continue
            score = fuzz.ratio(ref, inp)
            if score > best_score:
                best_tok, best_score = inp, score
        if best_score >= threshold and best_tok is not None:
            mapping[ref] = best_tok
            used.add(best_tok)
    return mapping


def _is_numeric(x) -> bool:
    try:
        float(x)
        return True
    except (TypeError, ValueError):
        return False


# ─────────────────────────────────────────────────────────────────────────────
# Step 1 — detect whether ingredient order is flipped vs RxNorm
# ─────────────────────────────────────────────────────────────────────────────

def _order_flipped(
    input_term: str | list | tuple,
    matched_term: str | None,
    threshold: int = 80,
) -> bool:
    """
    Returns True if the ingredients appear in a different order in the
    input vs the matched RxNorm string, even accounting for misspellings.

    e.g. "levidopa/carbidopa" matched to "carbidopa / levodopa" -> True
         "carbidopa/levodopa" matched to "carbidopa / levodopa" -> False
    """
    if not isinstance(matched_term, (list, tuple)) and pd.isna(matched_term):
        return False

    if isinstance(input_term, (list, tuple)):
        input_str = " ".join(str(x) for x in input_term)
    else:
        input_str = str(input_term)

    input_tokens   = _tokens(input_str)
    matched_tokens = _tokens(str(matched_term))

    if len(matched_tokens) < 2:
        return False

    mapping = _fuzzy_token_match(input_tokens, matched_tokens, threshold)

    if len(mapping) < 2:
        return False

    input_order_of_matched = sorted(
        mapping.keys(),
        key=lambda ref: input_tokens.index(mapping[ref]),
    )

    return input_order_of_matched != matched_tokens


def _apply_order_flipped(
    df: pd.DataFrame,
    input_col: str,
    match_col: str,
) -> pd.DataFrame:
    df["token_order_flipped"] = df.apply(
        lambda row: _order_flipped(row[input_col], row[match_col]),
        axis=1,
    )
    n_flipped = int(df["token_order_flipped"].sum())
    logger.info("token_order_flipped: %d/%d rows flagged", n_flipped, len(df))
    return df


# ─────────────────────────────────────────────────────────────────────────────
# Step 2 — reorder dose values to match RxNorm ingredient order
# ─────────────────────────────────────────────────────────────────────────────

def _get_reorder_index(
    input_term: str,
    matched_term: str,
    threshold: int = 80,
) -> list[int] | None:
    """
    Compute the index permutation needed to reorder a dose list that is
    currently ordered according to input_term's ingredient order, so that
    it instead matches matched_term's ingredient order.

    e.g. input_term   = "levodopa/carbidopa/entacapone"   (dose order: levo, carb, enta)
         matched_term  = "carbidopa / entacapone / levodopa"
         -> returns [1, 2, 0]
            (dose[1]=carb first, dose[2]=enta second, dose[0]=levo third)
    """
    input_tokens   = _tokens(input_term)
    matched_tokens = _tokens(matched_term)

    if len(input_tokens) != len(matched_tokens):
        return None

    mapping = _fuzzy_token_match(input_tokens, matched_tokens, threshold)

    if len(mapping) != len(matched_tokens):
        return None

    try:
        index_order = [input_tokens.index(mapping[ref]) for ref in matched_tokens]
    except ValueError:
        return None

    if sorted(index_order) != list(range(len(matched_tokens))):
        return None

    return index_order


def _reorder_dose_for_swap(dose: list, index_order: list[int] | None = None) -> list:
    """
        Reorder a dose list when ingredient order was flipped.

    Handles:
      - list of numeric values:            [150, 37.5]   -> reordered by index_order
      - list with single slash-joined str: ['150/37.5']  -> reordered by index_order
      - single-value list (no swap):       ['187.5']     -> unchanged

    index_order must be provided for 3+ ingredients; falls back to a simple
    2-item reversal when None
    """
    
    if not isinstance(dose, list) or len(dose) == 0:
        return dose

    # FORMAT A: list of separate numeric values
    if all(_is_numeric(d) for d in dose) and len(dose) > 1:
        if index_order is not None and len(index_order) == len(dose):
            return [dose[i] for i in index_order]
        if index_order is None and len(dose) == 2:
            return [dose[1], dose[0]]
        return dose

    # FORMAT B: single slash-separated string, e.g. ['100/25/200']
    if len(dose) == 1 and isinstance(dose[0], str):
        raw = dose[0].strip()
        m = re.match(r'^([\d./]+)\s*([a-zA-Zµ%]*)\s*$', raw)
        if not m:
            return dose

        numbers = m.group(1).split('/')
        unit    = m.group(2).strip()

        if len(numbers) < 2:
            return dose

        if index_order is not None and len(index_order) == len(numbers):
            reordered = [numbers[i] for i in index_order]
        elif index_order is None and len(numbers) == 2:
            reordered = [numbers[1], numbers[0]]
        else:
            return dose

        rejoined = '/'.join(reordered)
        if unit:
            rejoined = f"{rejoined} {unit}"
        return [rejoined]

    return dose


def _apply_dose_reorder(
    df: pd.DataFrame,
    dose_col: str,
    input_col: str,
    matched_col: str,
    flag_col: str = "token_order_flipped",
    out_col: str = "dose_reordered",
) -> pd.DataFrame:
    # dose col may arrive as a stringified list when loaded from CSV
    df["dose"] = df["dose"].apply(
        lambda x: ast.literal_eval(x) if isinstance(x, str) else x
    )

    def _reorder_row(row):
        if not row[flag_col]:
            return row[dose_col]
        index_order = _get_reorder_index(row[input_col], row[matched_col])
        return _reorder_dose_for_swap(row[dose_col], index_order)

    df[out_col] = df.apply(_reorder_row, axis=1)
    n_reordered = int((df[out_col] != df[dose_col]).sum())
    logger.info("dose_reordered: %d/%d rows reordered", n_reordered, len(df))
    return df


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def apply_reorder_dose(
    df: pd.DataFrame,
    input_col: str,
    match_col: str,
    dose_col: str = "dose",
    out_col: str = "dose_reordered",
) -> pd.DataFrame:
    """
    Detect whether drug ingredients appear in a different order than the matched
    RxNorm term, then reorder the dose values to match the RxNorm ordering.

    Adds columns:
        token_order_flipped : bool — True if input order differs from RxNorm
        dose_reordered      : list — dose reordered to match RxNorm ingredient order
    """
    df = df.copy()
    df = _apply_order_flipped(df, input_col=input_col, match_col=match_col)
    df = _apply_dose_reorder(df, dose_col=dose_col, input_col=input_col, matched_col=match_col, out_col=out_col)
    return df
