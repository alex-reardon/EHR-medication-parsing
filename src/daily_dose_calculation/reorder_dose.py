from __future__ import annotations
import re
from rapidfuzz import fuzz
import ast

def _is_numeric(x):
    try:
        float(x)
        return True
    except (TypeError, ValueError):
        return False



def _tokens(text: str) -> list[str]:
    return re.findall(r'[a-z]+', text.lower())


def _fuzzy_token_match(input_tokens: list[str], ref_tokens: list[str], threshold: int = 80) -> dict[str, str]:
    """Map each ref_token to its best-matching input_token above threshold."""
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


def _get_reorder_index(input_term: str, matched_term: str, threshold: int = 80) -> list[int] | None:
    """
    Compute the index permutation needed to reorder a dose list that is
    currently ordered according to input_term's ingredient order, so that
    it instead matches matched_term's ingredient order.

    e.g. input_term  = "levodopa/carbidopa/entacapone"   (dose order: levo, carb, enta)
         matched_term = "carbidopa / entacapone / levodopa"
         -> returns [1, 2, 0]
            (dose[1]=carb goes first, dose[2]=enta goes second, dose[0]=levo goes third)
    """




    input_tokens   = _tokens(input_term)
    matched_tokens = _tokens(matched_term)

    if len(input_tokens) != len(matched_tokens):
        return None

    mapping = _fuzzy_token_match(input_tokens, matched_tokens, threshold)

    if len(mapping) != len(matched_tokens):
        return None  # couldn't confidently pair every token

    try:
        index_order = [input_tokens.index(mapping[ref]) for ref in matched_tokens]
    except ValueError:
        return None

    # sanity check: must be a valid permutation (no dupes, covers full range)
    if sorted(index_order) != list(range(len(matched_tokens))):
        return None


    
    # # TEMP debug
    # if input_term.startswith('lev') :
    #     print("input_term", input_term)
    #     print("index_order", index_order)
    # # TEMP debug


    return index_order



def _reorder_dose_for_swap(dose, index_order: list[int] | None = None):
    """
    Reorder a slash-separated dose string when token order was flipped.

    Handles:
      - list of numeric values:           [150, 37.5]      -> reordered by index_order
      - list with single slash-joined str: ['150/37.5']     -> reordered by index_order
      - single-value list (no swap needed): ['187.5']       -> unchanged

    Parameters
    ----------
    dose : list
        Value from the dose column.
    index_order : list[int] | None
        Permutation indices to apply. If None, falls back to a simple
        2-item reversal (legacy pair-swap behavior). For 3+ ingredients,
        index_order MUST be provided — there's no way to infer a unique
        3-item permutation from length alone.

    Returns
    -------
    list
        Reordered dose, same shape as input.
    """

        
    if not isinstance(dose, list) or len(dose) == 0:
        return dose

    # ---------------------------------------------------------
    # FORMAT A: list of separate numeric values
    # ---------------------------------------------------------
    if all(_is_numeric(d) for d in dose) and len(dose) > 1:

        if index_order is not None and len(index_order) == len(dose):
            return [dose[i] for i in index_order]

        if index_order is None and len(dose) == 2:
            return [dose[1], dose[0]]  # legacy pair fallback
        return dose  # can't safely reorder without explicit index_order

    # ---------------------------------------------------------
    # FORMAT B: single slash-separated string, e.g. ['100/25/200']
    # ---------------------------------------------------------
    if len(dose) == 1 and isinstance(dose[0], str):

        raw = dose[0].strip()

        m = re.match(
            r'^([\d./]+)\s*([a-zA-Zµ%]*)\s*$',
            raw
        )

        if not m:
            return dose

        numbers = m.group(1).split('/')
        unit = m.group(2).strip()

        if len(numbers) < 2:
            return dose  # single value, nothing to reorder

        if index_order is not None and len(index_order) == len(numbers):
            reordered = [numbers[i] for i in index_order]
        elif index_order is None and len(numbers) == 2:
            reordered = [numbers[1], numbers[0]]  # legacy pair fallback
        else:
            return dose  # can't safely reorder without explicit index_order

        rejoined = '/'.join(reordered)

        if unit:
            rejoined = f"{rejoined} {unit}"
        return [rejoined]
    return dose




def apply_dose_reorder(
    df,
    dose_col,
    input_col,
    matched_col,
    flag_col="token_order_flipped",
    out_col="dose_reordered",
):
    df = df.copy()
    df["dose"] = df["dose"].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x) # make sure dose col is list


    def _reorder_row(row):
        if not row[flag_col]:
            return row[dose_col]

        index_order = _get_reorder_index(
            row[input_col],
            row[matched_col],
        )
        return _reorder_dose_for_swap(row[dose_col], index_order)

    df[out_col] = df.apply(_reorder_row, axis=1)

    return df

