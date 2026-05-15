import re
import pandas as pd


# =========================================================
# GLOBALS
# =========================================================
NUM = r'(?:\d+(?:\.\d+)?|\.\d+)'
SEP = r'\s*[/\-]\s*'


# =========================================================
# BUILD UNIT PATTERN
# FROM COMPILED RULES
# =========================================================
def build_unit_pattern(
    compiled_rules
):
    """
    Build unit regex pattern from
    compiled rule objects.
    """

    unit_values = [

        rule["replacement"]

        for rule in compiled_rules

        if pd.notna(
            rule["replacement"]
        )
    ]

    # -----------------------------------------------------
    # DEDUPE PRESERVE ORDER
    # -----------------------------------------------------
    unit_values = list(
        dict.fromkeys(unit_values)
    )

    # -----------------------------------------------------
    # LONGEST FIRST
    # IMPORTANT
    # -----------------------------------------------------
    unit_values = sorted(
        unit_values,
        key=len,
        reverse=True
    )

    # -----------------------------------------------------
    # BUILD PATTERN
    # -----------------------------------------------------
    unit_pattern = (
        r'(?:'
        + '|'.join(
            map(re.escape, unit_values)
        )
        + r')'
    )

    return unit_pattern



# =========================================================
# EXTRACT DOSES
# =========================================================
def remove_dose_and_units(
    text: str,
    unit_pattern: str
):

    if text is None or (
        isinstance(text, float)
        and pd.isna(text)
    ):

        return pd.Series([
            None,
            text
        ])

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

    matches = list(
        re.finditer(
            ratio_unit_each_pattern,
            text,
            flags=re.VERBOSE
        )
    )

    for match in matches:

        full_match = match.group(0)

        parts = re.split(
            SEP,
            full_match
        )

        for part in parts:

            m = re.match(
                rf'({NUM})\s*({unit_pattern})',
                part
            )

            if not m:
                continue

            parsed_doses.append({

                "dose": m.group(1),

                "unit": m.group(2),

                "raw": part
            })

    text = re.sub(
        ratio_unit_each_pattern,
        ' ',
        text,
        flags=re.VERBOSE
    )

    # =====================================================
    # 1B. RATIOS WITH SHARED UNIT
    # ex:
    # 25/100 mg
    # 5/7.5 mg
    # =====================================================

    ratio_pattern = rf'''
    (
        {NUM}
        (?:{SEP}{NUM})+
    )
    \s*
    ({unit_pattern})
    '''

    matches = list(
        re.finditer(
            ratio_pattern,
            text,
            flags=re.VERBOSE
        )
    )

    for match in matches:

        ratio = match.group(1)

        unit = match.group(2)

        parts = re.split(
            SEP,
            ratio
        )

        # ---------------------------------------------
        # NORMALIZE NUMBERS
        # ---------------------------------------------

        normalized_doses = []

        for p in parts:

            try:

                p = float(p)

                if p.is_integer():
                    p = int(p)

            except:
                pass

            normalized_doses.append(p)

        # ---------------------------------------------
        # STORE SHARED-UNIT RATIO
        # ---------------------------------------------

        parsed_doses.append({

            "dose": normalized_doses,

            "unit": [unit],

            "raw": f"{ratio} {unit}"
        })

    # -------------------------------------------------
    # REMOVE MATCHED SPANS
    # -------------------------------------------------

    text = re.sub(
        ratio_pattern,
        ' ',
        text,
        flags=re.VERBOSE
    )

    # =====================================================
    # 1C. RATIOS WITHOUT UNITS
    # ex: 25/100
    # =====================================================
    ratio_no_unit_sep = r'\s*/\s*'

    ratio_no_unit_pattern = rf'''
    \b
    {NUM}
    (?:{ratio_no_unit_sep}{NUM})+
    \b
    (?!\s*{unit_pattern})
    '''

    matches = re.findall(
        ratio_no_unit_pattern,
        text,
        flags=re.VERBOSE
    )

    for ratio in matches:

        parts = re.split(
            SEP,
            ratio
        )

        for p in parts:

            parsed_doses.append({

                "dose": p,

                "unit": None,

                "raw": p
            })

    text = re.sub(
        ratio_no_unit_pattern,
        ' ',
        text,
        flags=re.VERBOSE
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

    matches = list(
        re.finditer(
            standard_pattern,
            text,
            flags=re.VERBOSE
        )
    )

    for match in matches:

        parsed_doses.append({

            "dose": match.group(1),

            "unit": match.group(2),

            "raw": match.group(0)
        })

    # =====================================================
    # REMOVE MATCHED DOSES
    # =====================================================
    clean_text = re.sub(
        standard_pattern,
        ' ',
        text,
        flags=re.VERBOSE
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
            unit_only_pattern,
            ' ',
            clean_text,
            flags=re.VERBOSE
        )



    # =====================================================
    # FLATTEN OUTPUTS
    # =====================================================
    doses = [
        d["raw"]
        for d in parsed_doses
    ]

    return pd.Series([
        parsed_doses if parsed_doses else None,
        doses if doses else None,
        clean_text
    ])


# =========================================================
# APPLY TO DATAFRAME
# =========================================================
def extract_dose(
    df: pd.DataFrame,
    compiled_rules
):
    """
    Apply dose extraction using
    compiled unit rules.
    """

    df = df.copy()

    # -----------------------------------------------------
    # BUILD UNIT PATTERN
    # -----------------------------------------------------
    unit_pattern = build_unit_pattern(
        compiled_rules
    )

    # -----------------------------------------------------
    # APPLY EXTRACTION
    # -----------------------------------------------------
    df[[
        "parsed_doses",
        "dose",
        "clean_text"
    ]] = df["clean_text"].apply(
        lambda x: remove_dose_and_units(
            x,
            unit_pattern
        )
    )

    # -----------------------------------------------------
    # METRICS
    # -----------------------------------------------------
    mapped = df["dose"].notna().sum()

    print(
        f"Dose Extraction Complete: "
        f"{mapped}/{len(df)} rows mapped "
        f"({mapped/len(df):.2%})"
    )

    return df