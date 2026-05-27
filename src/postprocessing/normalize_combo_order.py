import re
import pandas as pd
from rapidfuzz import fuzz


# ==========================================================
# TARGETS
# ==========================================================
TARGETS = ["carbidopa", "levodopa", "entacapone", "benserazide"]


# ==========================================================
# DOSE REORDER MAP
# ==========================================================
DOSE_REORDER_MAP = {
    "triple_forward": [0, 2, 1],
    "triple_reverse": [1, 2, 0],
    "pair_reverse":   [1, 0],
    "pair_reverse_benserazide": [1, 0],
}


# ==========================================================
# CANONICAL NAME MAP
# ==========================================================
CANONICAL_ORDER = {
    "pair_reverse":             "carbidopa/levodopa",
    "triple_forward":           "carbidopa/entacapone/levodopa",
    "triple_reverse":           "carbidopa/entacapone/levodopa",
    "pair_reverse_benserazide": "benserazide/levodopa",
}


# ==========================================================
# NORMALIZE NAME ORDER (exact regex)
# ==========================================================
def normalize_dose_order(text):

    if not isinstance(text, str):
        return text

    text = text.lower()



    # -----------------------------------------
    # strip numbers jammed onto ingredient names
    # -----------------------------------------
    for target in TARGETS:
        text = re.sub(
            rf'{target}\d+',
            target,
            text,
            flags=re.I
        )

    # ==========================================================
    # CASE 2 — run BEFORE case 1
    # carbidopa/levodopa/entacapone
    # -> carbidopa/entacapone/levodopa
    # ==========================================================
    pattern_triple = re.compile(
        r'''
        carbidopa
        \s*[/\-]\s*
        levodopa
        \s*[/\-]\s*
        entacapone
        ''',
        flags=re.I | re.X
    )

    text = pattern_triple.sub(
        "carbidopa/entacapone/levodopa",
        text
    )

    # ==========================================================
    # CASE 3 — run BEFORE case 1
    # levodopa/carbidopa/entacapone
    # -> carbidopa/entacapone/levodopa
    # ==========================================================
    pattern_reverse_triple = re.compile(
        r'''
        levodopa
        \s*(?:/|\s+)\s*
        carbidopa
        \s*(?:/|\s+)\s*
        entacapone
        ''',
        flags=re.I | re.X
    )

    text = pattern_reverse_triple.sub(
        "carbidopa/entacapone/levodopa",
        text
    )

    # ==========================================================
    # CASE 1 — run LAST
    # levodopa/carbidopa
    # -> carbidopa/levodopa
    # ==========================================================
    pattern_reverse_pair = re.compile(
        r'''
        levodopa
        \s*(?:/|\s+)\s*
        carbidopa
        ''',
        flags=re.I | re.X
    )

    text = pattern_reverse_pair.sub(
        "carbidopa/levodopa",
        text
    )

    # ==========================================================
    # CASE 4
    # levodopa/benserazide
    # -> benserazide/levodopa
    # ==========================================================
    pattern_levo_bens = re.compile(
        r'''
        levodopa
        \s*(?:/|\s+)\s*
        benserazide
        ''',
        flags=re.I | re.X
    )

    text = pattern_levo_bens.sub(
        "benserazide/levodopa",
        text
    )

    return text


# ==========================================================
# FUZZY INGREDIENT DETECTION
# ==========================================================
def _detect_ingredients(text, threshold=80):

    if not isinstance(text, str):
        return []

    found = []

    for i, word in enumerate(re.findall(r'[a-z]+', text.lower())):

        for target in TARGETS:

            if fuzz.ratio(word, target) >= threshold:
                found.append((i, target))
                break

    return [target for _, target in sorted(found)]


def _detect_case(text, threshold=80):

    if not isinstance(text, str):
        return None

    ingredients = _detect_ingredients(text, threshold)

    # -------------------------------------------------
    # TRIPLES
    # -------------------------------------------------
    if set(ingredients) == {"carbidopa", "levodopa", "entacapone"}:

        if ingredients[0] == "carbidopa":
            return "triple_forward"

        if ingredients[0] == "levodopa":
            return "triple_reverse"

    # -------------------------------------------------
    # CARBIDOPA/LEVODOPA PAIR
    # -------------------------------------------------
    if (
        set(ingredients) == {"carbidopa", "levodopa"}
        and ingredients[0] == "levodopa"
    ):
        return "pair_reverse"

    # -------------------------------------------------
    # BENSERAZIDE/LEVODOPA PAIR
    # -------------------------------------------------
    if (
        set(ingredients) == {"benserazide", "levodopa"}
        and ingredients[0] == "levodopa"
    ):
        return "pair_reverse_benserazide"

    return None


# ==========================================================
# FUZZY NAME NORMALIZATION
# ==========================================================
def _fuzzy_normalize_names(text, case, threshold=80):

    if not isinstance(text, str) or case is None:
        return text

    canonical = CANONICAL_ORDER.get(case)

    if canonical is None:
        return text

    n_ingredients = len(canonical.split('/'))

    token = r'[a-z]+'
    sep = r'[\s/\-]+'
    ingredient_block = sep.join([token] * n_ingredients)

    pattern = re.compile(ingredient_block, flags=re.I)

    def replacer(m):

        words = re.findall(r'[a-z]+', m.group(0).lower())

        matched = []

        for word in words:

            best = max(
                TARGETS,
                key=lambda t: fuzz.ratio(word, t)
            )

            if fuzz.ratio(word, best) >= threshold:
                matched.append(best)
            else:
                return m.group(0)

        expected = set(canonical.split('/'))

        if set(matched) != expected:
            return m.group(0)

        return canonical

    return pattern.sub(replacer, text)


# ==========================================================
# DOSE REORDER HELPERS
# ==========================================================
def _is_numeric(x):
    try:
        float(x)
        return True
    except (TypeError, ValueError):
        return False


def _reorder_doses(doses, index_order):

    if not isinstance(doses, list) or len(doses) == 0:
        return doses

    # FORMAT A: list of numerics or numeric strings
    if (
        len(doses) == len(index_order)
        and all(_is_numeric(d) for d in doses)
    ):
        return [doses[i] for i in index_order]

    # FORMAT B: single slash-separated string
    if len(doses) == 1 and isinstance(doses[0], str):

        raw = doses[0].strip()

        m = re.match(
            r'^([\d./]+)\s*([a-zA-Zµ%]*)\s*$',
            raw
        )

        if not m:
            return doses

        numbers = m.group(1).split('/')
        unit = m.group(2).strip()

        if len(numbers) != len(index_order):
            return doses

        reordered = [numbers[i] for i in index_order]
        rejoined = '/'.join(reordered)

        if unit:
            rejoined = f"{rejoined} {unit}"

        return [rejoined]

    return doses


# ==========================================================
# APPLY
# ==========================================================
def apply_normalize_dose_order(
    df: pd.DataFrame,
    col: str = "clean_text",
    dose_col: str = "dose",
    out_dose_col: str = "dose_reordered"
) -> pd.DataFrame:

    df = df.copy()

    before = df[col].copy()

    # -----------------------------------------------------
    # DETECT CASE BEFORE REWRITING NAMES
    # -----------------------------------------------------
    cases = before.apply(_detect_case)

    # -----------------------------------------------------
    # EXACT REGEX NORMALIZATION
    # -----------------------------------------------------
    df[col] = df[col].apply(normalize_dose_order)

    # -----------------------------------------------------
    # FUZZY NORMALIZATION
    # catches misspellings exact regex missed
    # -----------------------------------------------------
    df[col] = df.apply(
        lambda row: _fuzzy_normalize_names(
            row[col],
            cases[row.name]
        ),
        axis=1
    )

    # -----------------------------------------------------
    # REORDER DOSES
    # -----------------------------------------------------
    df[out_dose_col] = df[dose_col]

    reorder_mask = cases.notna()

    def reorder_row(row):

        case = cases[row.name]
        index_order = DOSE_REORDER_MAP.get(case)

        if index_order is None:
            return row[dose_col]

        return _reorder_doses(row[dose_col], index_order)

    df.loc[reorder_mask, out_dose_col] = (
        df[reorder_mask].apply(reorder_row, axis=1)
    )

    # -----------------------------------------------------
    # METRICS
    # -----------------------------------------------------
    changed = (df[col] != before).sum()

    print(
        f"Dose Order Normalization Complete: "
        f"{changed}/{len(df)} rows changed "
        f"({changed/len(df):.2%})"
    )

    return df