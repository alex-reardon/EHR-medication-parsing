from __future__ import annotations
import re
import pandas as pd
from rapidfuzz import fuzz

# Did the medication ingredients appear in a different order than the matched RxNorm drug?"


def _tokens(text: str) -> list[str]:
    """Extract alphabetic tokens from a string, lowercased."""
    return re.findall(r'[a-z]+', text.lower())



def _fuzzy_token_match(input_tokens: list[str], ref_tokens: list[str], threshold: int = 80) -> dict[str, str]:
    """
    Map each ref_token to its best-matching input_token above threshold.
    Returns {ref_token: input_token} for matched pairs.
    """
    mapping = {}
    used = set()
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



def _order_flipped(input_term: str | list | tuple, matched_term: str | None, threshold: int = 80) -> bool:
    """
    Returns True if the ingredients appear in a different order in the
    input vs the matched RxNorm string, even accounting for misspellings.

    e.g. "levidopa/carbidopa" matched to "carbidopa / levodopa" → True
         "carbidopa/levodopa" matched to "carbidopa / levodopa" → False
    """

    try:
        if pd.isna(matched_term):
            return False
    except TypeError:
        pass  # lists/tuples raise TypeError in pd.isna, which means it's not NaN

    if isinstance(input_term, (list, tuple)):
        input_str = " ".join(str(x) for x in input_term)
    else:
        input_str = str(input_term)

    input_tokens   = _tokens(input_str)
    matched_tokens = _tokens(matched_term)

    if len(matched_tokens) < 2:
        return False

    # fuzzy-map each matched token → its closest input token
    mapping = _fuzzy_token_match(input_tokens, matched_tokens, threshold)

    if len(mapping) < 2:
        return False  # couldn't confidently pair enough tokens

    # reconstruct the order each matched token's counterpart appeared in the input
    input_order_of_matched = sorted(
        mapping.keys(),
        key=lambda ref: input_tokens.index(mapping[ref])
    )

    return input_order_of_matched != matched_tokens




def apply_order_flipped(df, input_col, match_col) :
    df[f"token_order_flipped"] = df.apply(
        lambda row: _order_flipped(row[input_col], row[match_col]),
        axis=1,
    )

    return df 
