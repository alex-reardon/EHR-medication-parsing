import logging
import re
import pandas as pd

logger = logging.getLogger(__name__)


# =========================================================
# GLOBALS
# =========================================================
NUM = r'(?:\d+(?:\.\d+)?|\.\d+)'
SEP = r'\s*[/\-]\s*'


# =========================================================
# BUILD UNIT PATTERN FROM COMPILED RULES
# =========================================================
def _build_unit_regex(compiled_rules):
    rule_map = [
        (rule["pattern"], rule["replacement"])
        for rule in compiled_rules
        if pd.notna(rule.get("replacement"))
        and rule.get("pattern") is not None
    ]

    pattern_raws = sorted(
        [
            rule["pattern_raw"]
            for rule in compiled_rules
            if rule.get("pattern_raw")
        ],
        key=len,
        reverse=True
    )

    unit_pattern = (
        r'(?:'
        + '|'.join(pattern_raws)
        + r')'
    )

    return unit_pattern, rule_map


# =========================================================
# NORMALIZE UNIT
# =========================================================
def _normalize_unit(raw_unit: str, rule_map: list) -> str:
    for pattern, replacement in rule_map:
        if pattern.fullmatch(raw_unit.strip()):
            return replacement
    return raw_unit.lower()


# =========================================================
# NORMALIZE DOSE STRING
# Always produces "num1/num2/num3" format
# =========================================================
def _normalize_dose_str(parts: list) -> str:
    """
    Normalize a list of dose component strings into a
    single consistent '/'-separated string.

    [100, 25]     → '100/25'
    ['100', '25'] → '100/25'
    ['81']        → '81'
    [25.0]        → '25'
    """
    normalized = []
    for p in parts:
        try:
            val = float(str(p))
            normalized.append(str(int(val)) if val.is_integer() else str(val))
        except (ValueError, TypeError):
            normalized.append(str(p).strip())
    return "/".join(normalized)


# =========================================================
# EXTRACT DOSES
# =========================================================
def extract_dose(
    text: str,
    unit_pattern: str,
    rule_map: dict
):
    if text is None or (
        isinstance(text, float)
        and pd.isna(text)
    ):
        return pd.Series([None, None, text])

    text = str(text).lower()
    parsed_doses = []

    # =====================================================
    # 1A. RATIOS WITH UNITS ATTACHED
    # ex: 25mg/100mg
    # =====================================================
    ratio_unit_each_pattern = rf'''
    (
        {NUM}\s*{unit_pattern}
        (?:{SEP}
        {NUM}\s*{unit_pattern})+
    )
    '''

    matches = list(re.finditer(
        ratio_unit_each_pattern, text, flags=re.VERBOSE
    ))

    for match in matches:
        full_match = match.group(0)
        parts = re.split(SEP, full_match)

        dose_parts = []
        units = []

        for part in parts:
            m = re.match(rf'({NUM})\s*({unit_pattern})', part)
            if not m:
                continue
            dose_parts.append(m.group(1))
            units.append(_normalize_unit(m.group(2), rule_map))

        normalized = _normalize_dose_str(dose_parts)
        # use first unit as canonical (all should match for same-drug ratios)
        unit = units[0] if units else None

        parsed_doses.append({
            "dose": normalized,
            "unit": unit,
            "raw":  normalized + (" " + unit if unit else "")
        })

    text = re.sub(
        ratio_unit_each_pattern, ' ', text, flags=re.VERBOSE
    )

    # =====================================================
    # 1B. RATIOS WITH SHARED UNIT
    # ex: 25/100 mg, 5/7.5 mg
    # =====================================================
    ratio_pattern = rf'''
    (
        {NUM}
        (?:{SEP}{NUM})+
    )
    \s*
    ({unit_pattern})
    '''

    matches = list(re.finditer(
        ratio_pattern, text, flags=re.VERBOSE
    ))

    for match in matches:
        ratio = match.group(1)
        unit  = _normalize_unit(match.group(2), rule_map)
        parts = re.split(SEP, ratio)

        normalized = _normalize_dose_str(parts)

        parsed_doses.append({
            "dose": normalized,
            "unit": unit,
            "raw":  normalized + " " + match.group(2)
        })

    text = re.sub(ratio_pattern, ' ', text, flags=re.VERBOSE)

    # =====================================================
    # 1C. RATIOS WITHOUT UNITS
    # ex: 25/100
    # =====================================================
    ratio_no_unit_sep     = SEP
    ratio_no_unit_pattern = rf'''
    \b
    {NUM}
    (?:{ratio_no_unit_sep}{NUM})+
    \b
    (?!\s*{unit_pattern})
    '''

    matches = re.findall(
        ratio_no_unit_pattern, text, flags=re.VERBOSE
    )

    for ratio in matches:
        parts      = re.split(SEP, ratio)
        normalized = _normalize_dose_str(parts)

        parsed_doses.append({
            "dose": normalized,
            "unit": None,
            "raw":  normalized
        })

    text = re.sub(
        ratio_no_unit_pattern, ' ', text, flags=re.VERBOSE
    )

    # =====================================================
    # 2. STANDARD DOSES
    # ex: 137 mg
    # =====================================================
    standard_pattern = rf'''
    ({NUM})
    \s*
    ({unit_pattern})
    '''

    matches = list(re.finditer(
        standard_pattern, text, flags=re.VERBOSE
    ))

    for match in matches:
        normalized = _normalize_dose_str([match.group(1)])
        unit       = _normalize_unit(match.group(2), rule_map)

        parsed_doses.append({
            "dose": normalized,
            "unit": unit,
            "raw":  normalized + " " + match.group(2)
        })

    clean_text = re.sub(
        standard_pattern, ' ', text, flags=re.VERBOSE
    )

    # =====================================================
    # REMOVE STANDALONE UNITS
    # =====================================================
    if unit_pattern:
        unit_only_pattern = rf'''
        \b
        {unit_pattern}
        (?:/{unit_pattern})*
        \b
        '''
        clean_text = re.sub(
            unit_only_pattern, ' ', clean_text, flags=re.VERBOSE
        )

    # =====================================================
    # FLATTEN OUTPUTS
    # dose col is now always a list of '/'-separated strings
    # e.g. ['100/25', '81', '25/100/10']
    # =====================================================
    doses = [d["dose"] for d in parsed_doses]

    return pd.Series([
        parsed_doses if parsed_doses else None,
        doses        if doses        else None,
        clean_text
    ])


# =========================================================
# APPLY TO DATAFRAME
# =========================================================
def apply_dose_extraction(df: pd.DataFrame, compiled_rules):

    df = df.copy()

    unit_pattern, rule_map = _build_unit_regex(compiled_rules)

    df[["parsed_doses", "dose", "clean_text"]] = df["clean_text"].apply(
        lambda x: extract_dose(x, unit_pattern, rule_map)
    )

    mapped = df["dose"].notna().sum()
    logger.info(
        "Dose Extraction Complete: %d/%d rows mapped (%.2f%%)",
        mapped, len(df), 100 * mapped / len(df)
    )

    return df