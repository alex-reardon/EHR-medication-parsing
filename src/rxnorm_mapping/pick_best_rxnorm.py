import pandas as pd



def remove_list_format(x):

    # missing
    if pd.isna(x):
        return x

    # actual python list only
    if isinstance(x, list):

        # single element
        if len(x) == 1:
            return x[0]

        # multiple elements
        return ", ".join(map(str, x))

    return x





def pick_best_rxnorm(
    df: pd.DataFrame,
    col_str_name : str, 
    prefix0: str = "0",
    prefix1: str = "1",
    out_cols=("rxmatch", "rxcui", "score", "tty")
) -> pd.DataFrame:
    """
    Select best RxNorm match between two candidates per row using priority:
    MIN > IN > BN, then highest score.

    Creates:
        final

    Logic:
    - if prefix0 wins:
        final = paren_text

    - elif prefix1 wins:
        final = col_str_name + 'no_time'

    - else:
        final = col_str_name + 'no_time'
    """

    priority = {"MIN": 0, "IN": 1, "BN": 2}

    def pick(row):

        # -------------------------
        # get values
        # -------------------------
        tty0 = row.get(f"tty{prefix0}")
        tty1 = row.get(f"tty{prefix1}")

        score0 = row.get(f"score{prefix0}")
        score1 = row.get(f"score{prefix1}")

        # handle None / NaN
        score0 = -1 if pd.isna(score0) else float(score0)
        score1 = -1 if pd.isna(score1) else float(score1)

        # -------------------------
        # assign priority
        # lower = better
        # -------------------------
        p0 = priority.get(tty0, 99)
        p1 = priority.get(tty1, 99)

        # ======================================================
        # PREFIX 1 WINS
        # ======================================================
        if (p1 < p0) or (p1 == p0 and score1 >= score0):

            winner = prefix1

            final = row.get(col_str_name + 'no_time')

            return pd.Series([
                row.get(f"rxmatch{winner}"),
                row.get(f"rxcui{winner}"),
                row.get(f"score{winner}"),
                row.get(f"tty{winner}"),
                final
            ])

        # ======================================================
        # PREFIX 0 WINS
        # ======================================================
        elif (p0 < p1) or (p0 == p1 and score0 > score1):

            winner = prefix0

            final = row.get("paren_text")

            return pd.Series([
                row.get(f"rxmatch{winner}"),
                row.get(f"rxcui{winner}"),
                row.get(f"score{winner}"),
                row.get(f"tty{winner}"),
                final
            ])

        # ======================================================
        # FALLBACK
        # ======================================================
        else:

            final = row.get(col_str_name + "no_time")

            return pd.Series([
                None,
                None,
                None,
                None,
                final
            ])

    df[list(out_cols) + ["final"]] = df.apply(
        pick,
        axis=1
    )

    df["final"] = df["final"].apply(remove_list_format)

    return df