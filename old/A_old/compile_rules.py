import re
import pandas as pd


# =========================================================
# GENERIC RULE COMPILER
# =========================================================
def compile_medication_rules(path):

    df = pd.read_csv(path, keep_default_na=False)
    df = df.fillna("")

    # -----------------------------------------------------
    # CLEAN
    # -----------------------------------------------------
    df = df.dropna(subset=["raw"]).copy()

    df["raw"] = (
        df["raw"]
        .astype(str)
        .str.strip()
    )

    if "replacement" in df.columns:
        df["replacement"] = (
            df["replacement"]
            .fillna("")
            .astype(str)
            .str.strip()
        )

    # -----------------------------------------------------
    # SORT LONGEST FIRST
    # prevents partial matches
    # -----------------------------------------------------
    df = df.sort_values(
        by="raw",
        key=lambda x: x.str.len(),
        ascending=False
    )

    compiled = {}

    # =====================================================
    # COMPILE EACH CATEGORY
    # =====================================================
    for category, group in df.groupby("category"):

        group = group.copy()

        # -------------------------------------------------
        # REPLACEMENT RULES
        # -------------------------------------------------
        compiled_rules = []

        for _, row in group.iterrows():

            pattern = row["raw"]

            replacement = (
                row["replacement"]
                if "replacement" in row
                else ""
            )

            compiled_rules.append({
                "pattern_raw": pattern,
                "pattern": re.compile(
                    pattern,
                    flags=re.IGNORECASE
                ),
                "replacement": replacement
            })

        compiled[category] = compiled_rules

    return compiled
