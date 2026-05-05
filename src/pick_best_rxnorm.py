import pandas as pd

def pick_best_rxnorm(
    df: pd.DataFrame,
    prefix0: str = "0",
    prefix1: str = "1",
    out_cols=("rxmatch", "rxcui", "score", "tty")
) -> pd.DataFrame:
    """
    Select best RxNorm match between two candidates per row using priority:
    MIN > IN > BN, then highest score.

    Assumes columns:
        rxmatch{0/1}, rxcui{0/1}, score{0/1}, tty{0/1}
    """

    priority = {"MIN": 0, "IN": 1, "BN": 2}

    def pick(row):
        # get values
        tty0 = row.get(f"tty{prefix0}")
        tty1 = row.get(f"tty{prefix1}")

        score0 = row.get(f"score{prefix0}", -1)
        score1 = row.get(f"score{prefix1}", -1)

        # assign priority (lower = better)
        p0 = priority.get(tty0, 99)
        p1 = priority.get(tty1, 99)

        # choose best
        if (p1 < p0) or (p1 == p0 and score1 >= score0):
            return pd.Series([
                row.get(f"rxmatch{prefix1}"),
                row.get(f"rxcui{prefix1}"),
                score1,
                tty1
            ])
        else:
            return pd.Series([
                row.get(f"rxmatch{prefix0}"),
                row.get(f"rxcui{prefix0}"),
                score0,
                tty0
            ])

    df[list(out_cols)] = df.apply(pick, axis=1)

    return df