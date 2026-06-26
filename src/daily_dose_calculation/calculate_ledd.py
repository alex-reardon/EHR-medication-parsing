import pandas as pd


def _has_entacapone(canonical: str) -> bool:
    if not isinstance(canonical, str):
        return False
    return "entacapone" in canonical.lower()


def _get_levodopa_dose(row, dose_cols=("daily_dose_1", "daily_dose_2", "daily_dose_3")):
    # if entacapone present, don't try to pick — leave as is
    if _has_entacapone(row.get("ledd_canonical", "")):
        return None

    non_null = [row[c] for c in dose_cols if pd.notna(row[c])]

    if not non_null:
        return None

    return max(float(v) for v in non_null)


def compute_levodopa_ledd(row, dose_cols=("daily_dose_1", "daily_dose_2", "daily_dose_3")):
    levodopa_dose = _get_levodopa_dose(row, dose_cols)

    if levodopa_dose is None or pd.isna(row["ledd_factor_numeric"]):
        return None

    try:
        return float(levodopa_dose) * float(row["ledd_factor_numeric"])
    except (TypeError, ValueError):
        return None


def apply_levodopa_ledd(df, dose_cols=("daily_dose_1", "daily_dose_2", "daily_dose_3")):
    df = df.copy()

    df["levodopa_dose"] = df.apply(
        lambda row: _get_levodopa_dose(row, dose_cols), axis=1
    )

    df["levodopa_ledd"] = df.apply(
        lambda row: compute_levodopa_ledd(row, dose_cols), axis=1
    )

    return df

#############old way WITHOUT MAX DOSE AS LEVODOPA
# import pandas as pd


# def _get_levodopa_index(canonical: str) -> int | None:
#     """
#     Find the position of 'levodopa' within a slash-separated canonical
#     ingredient string, e.g.:

#         "carbidopa / levodopa"               -> 1
#         "carbidopa/entacapone/levodopa"       -> 2
#         "benserazide/levodopa"                -> 1

#     Returns None if levodopa isn't present or string is malformed.
#     """
#     if not isinstance(canonical, str):
#         return None

#     parts = [p.strip().lower() for p in canonical.split('/')]

#     for i, p in enumerate(parts):
#         if p == "levodopa":
#             return i

#     return None



# def _get_levodopa_dose(row, dose_cols=("daily_dose_1", "daily_dose_2", "daily_dose_3")):
#     """
#     Return the levodopa-specific daily dose value for a row.

#     Priority:
#       1. If only ONE dose_col is non-null, use it directly
#          (single-value cases — e.g. plain levodopa with no combo,
#          or a row where only the total dose was captured).
#       2. Otherwise, use ledd_canonical's token position to pick
#          the correct dose_col.
#     """
#     non_null = [(c, row[c]) for c in dose_cols if pd.notna(row[c])]

#     # ---- case 1: only one dose value present, assume it's levodopa ----
#     if len(non_null) == 1:
#         return non_null[0][1]

#     # ---- case 2: use canonical position to pick the right column ----
#     idx = _get_levodopa_index(row["ledd_canonical"])

#     if idx is None or idx >= len(dose_cols):
#         return None

#     return row[dose_cols[idx]]



# def compute_levodopa_ledd(row, dose_cols=("daily_dose_1", "daily_dose_2", "daily_dose_3")):
#     levodopa_dose = _get_levodopa_dose(row, dose_cols)

#     if pd.isna(levodopa_dose) or pd.isna(row["ledd_factor_numeric"]):
#         return None

#     try:
#         return float(levodopa_dose) * float(row["ledd_factor_numeric"])
#     except (TypeError, ValueError):
#         return None



# def apply_levodopa_ledd(df, dose_cols=("daily_dose_1", "daily_dose_2", "daily_dose_3")):
#     df = df.copy()

#     df["levodopa_dose"] = df.apply(
#         lambda row: _get_levodopa_dose(row, dose_cols),
#         axis=1
#     )

#     df["levodopa_ledd"] = df.apply(
#         lambda row: compute_levodopa_ledd(row, dose_cols),
#         axis=1
#     )

    
#     df["levodopa_dose_confidence"] = df.apply(
#     lambda row: "single_value_assumed" if sum(pd.notna(row[c]) for c in dose_cols) == 1
#                 and len(str(row["ledd_canonical"]).split('/')) > 1
#     else "positional_match",
#     axis=1
#     )


#     return df

