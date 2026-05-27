import re
import pandas as pd
from rapidfuzz import fuzz
import ast



def reorder_combo_doses(
    df,
    dose_col="dose",
    rxmatch_col="rxmatch",
    med_string_col="med_string",
    out_col="dose_reordered",
    threshold=80
):

    # ---------------------------------------------------------
    # ingredient extraction
    # ---------------------------------------------------------
    def extract_ingredients(text):
        
        if pd.isna(text):
            return []

        text = str(text).lower()

        # extract ingredient tokens only
        return re.findall(r'[a-z]+', text)

    # ---------------------------------------------------------
    # reorder logic
    # ---------------------------------------------------------
    def reorder_row(row):

        doses = row[dose_col]
        rxmatch = row[rxmatch_col]
        med = row[med_string_col]

        # convert string representation of list
        # -------------------------
        # missing
        # -------------------------
        if doses is None:
            return doses

        if isinstance(doses, float) and pd.isna(doses):
            return doses

        # -------------------------
        # convert string list from CSV
        # -------------------------
        if isinstance(doses, str):

            try:
                doses = ast.literal_eval(doses)
            except:
                return doses

        # -------------------------
        # must now be list
        # -------------------------
        if not isinstance(doses, list):
            return doses

        med_ings = extract_ingredients(med)
        rx_ings = extract_ingredients(rxmatch)

        if len(doses) != len(med_ings):
            return doses

        if len(rx_ings) != len(med_ings):
            return doses

        reordered = []
        used = set()

        for rx_ing in rx_ings:

            # ---------------------------------------------
            # EXACT MATCH FIRST
            # ---------------------------------------------
            found = False

            for i, med_ing in enumerate(med_ings):

                if i in used:
                    continue

                if med_ing == rx_ing:

                    reordered.append(doses[i])

                    used.add(i)

                    found = True
                    break

            # ---------------------------------------------
            # FUZZY FALLBACK
            # ---------------------------------------------
            if not found:

                best_idx = None
                best_score = -1

                for i, med_ing in enumerate(med_ings):

                    if i in used:
                        continue

                    score = fuzz.ratio(rx_ing, med_ing)

                    if score > best_score:
                        best_score = score
                        best_idx = i

                if best_score < threshold:
                    return doses

                reordered.append(doses[best_idx])

                used.add(best_idx)

        return reordered

    df[out_col] = df.apply(
        reorder_row,
        axis=1
    )

    return df

    
def apply_reorder_combo_doses(
    df: pd.DataFrame,
    dose_col: str = "dose",
    rxmatch_col: str = "rxmatch",
    med_string_col: str = "med_string",
    out_col: str = "dose_reordered",
    threshold: int = 80
) -> pd.DataFrame:
    """
    Apply reorder_combo_doses to a DataFrame and print metrics.
    """

    df = reorder_combo_doses(
        df,
        dose_col=dose_col,
        rxmatch_col=rxmatch_col,
        med_string_col=med_string_col,
        out_col=out_col,
        threshold=threshold
    )

    # -----------------------------------------------------
    # METRICS
    # -----------------------------------------------------
    changed = (
        df[out_col].apply(str) != df[dose_col].apply(str)
    ).sum()

    print(
        f"Dose Reorder Complete: "
        f"{changed}/{len(df)} rows reordered "
        f"({changed/len(df):.2%})"
    )

    return df