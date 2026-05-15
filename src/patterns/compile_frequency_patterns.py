import re
import pandas as pd


# =========================================================
# COMPILE FREQUENCY RULES
# =========================================================
def build_frequency_pattern(path):

    df = pd.read_csv(
        path,
        keep_default_na=False
    )

    # -----------------------------------------------------
    # CLEAN
    # -----------------------------------------------------
    df = df.dropna(
        subset=["raw"]
    ).copy()

    df["raw"] = (
        df["raw"]
        .astype(str)
        .str.strip()
    )

    df["replacement"] = (
        df["replacement"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    compiled = {}

    # =====================================================
    # HELPER
    # =====================================================
    def compile_rule_group(group_df):

        group_df = group_df.sort_values(
            by="raw",
            key=lambda x: x.str.len(),
            ascending=False
        )

        return [

            {
                "pattern_raw": row["raw"],

                "pattern": re.compile(
                    row["raw"],
                    flags=re.IGNORECASE
                ),

                "replacement": row["replacement"]
            }

            for _, row in group_df.iterrows()
        ]

    # =====================================================
    # Frequency Primary
    # =====================================================
    frequency_primary_df = df[
        (df["category"] == "frequency")
        &
        (df["priority"] == 1)
    ].copy()

    compiled["frequency_primary"] = (
        compile_rule_group(frequency_primary_df)
    )

    # =====================================================
    # Frequency secondary 
    # =====================================================
    frequency_secondary_df = df[
        (df["category"] == "frequency")
        &
        (df["priority"] == 2)
    ].copy()

    compiled["frequency_secondary"] = (
        compile_rule_group(frequency_secondary_df)
    )

    # =====================================================
    # PRN
    # =====================================================
    prn_df = df[
        df["category"] == "prn"
    ].copy()

    compiled["prn"] = (
        compile_rule_group(prn_df)
    )

    # =====================================================
    # TIME OF DAY
    # =====================================================
    timing_df = df[
        df["category"] == "time_of_day"
    ].copy()

    compiled["time_of_day"] = (
        compile_rule_group(timing_df)
    )

    return compiled


# =========================================================
# BUILD SINGLE PATTERN
# FROM COMPILED RULES
# =========================================================
def compile_frequency_pattern(compiled_rules):

    terms = [

        rule["pattern_raw"]

        for rule in compiled_rules

        if pd.notna(rule["pattern_raw"])
    ]

    terms = sorted(
        list(dict.fromkeys(terms)),
        key=len,
        reverse=True
    )

    pattern = r"(?:{})".format(
        "|".join(terms)
    )

    return re.compile(
        pattern,
        flags=re.IGNORECASE
    )


# =========================================================
# BUILD TIMING PATTERN
# =========================================================
def build_timing_pattern(compiled_rules):

    grouped = {}

    # -----------------------------------------------------
    # GROUP RAW PATTERNS BY REPLACEMENT
    # -----------------------------------------------------
    for rule in compiled_rules:

        replacement = rule["replacement"]

        raw = rule["pattern_raw"]

        grouped.setdefault(
            replacement,
            []
        ).append(raw)

    timing_patterns = {}

    # -----------------------------------------------------
    # BUILD ONE REGEX PER TIMING LABEL
    # -----------------------------------------------------
    for label, patterns in grouped.items():

        patterns = sorted(
            list(dict.fromkeys(patterns)),
            key=len,
            reverse=True
        )

        combined = r"(?:{})".format(
            "|".join(patterns)
        )

        timing_patterns[label] = re.compile(
            combined,
            flags=re.IGNORECASE
        )

    return timing_patterns