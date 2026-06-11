import pandas as pd


def _normalize_list_field(x):

    # missing
    if x is None:
        return x

    # actual python list only
    if isinstance(x, list):

        # single element
        if len(x) == 1:
            return x[0]

        # multiple elements
        return ", ".join(map(str, x))

    return x


def apply_rxnorm_selector(
    df: pd.DataFrame,
    suffix_parenthetical_text: str = "parenthetical_text",
    suffix_clean_text: str = "clean_text",
    out_cols=("best_rxnorm_match", "best_rxcui", "best_score", "best_tty", "best_sbdf")
) -> pd.DataFrame:
    """
    Select best RxNorm match between two candidates per row using priority:
    BN > MIN > IN , then highest score.

    Creates:
        rxnorm_match
        rxcui
        score
        tty
        sbdf
        parsed

    Logic:
    - if suffix_parenthetical_text wins:
        parsed = parenthetical_text

    - elif suffix_clean_text wins:
        parsed = clean_text

    - else:
        parsed = clean_text
    """

    priority = {"BN": 0,  "MIN": 1, "IN": 2}

    def _select_best_match_row(row):

        # -------------------------------------------------
        # GET VALUES
        # -------------------------------------------------

        tty_parenthetical = row.get(f"tty{suffix_parenthetical_text}")
        tty_clean_text = row.get(f"tty{suffix_clean_text}")

        score_parenthetical = row.get(f"score{suffix_parenthetical_text}")
        score_clean_text = row.get(f"score{suffix_clean_text}")

        # -------------------------------------------------
        # HANDLE MISSING
        # -------------------------------------------------

        score_parenthetical = -1 if pd.isna(score_parenthetical) else float(score_parenthetical)
        score_clean_text = -1 if pd.isna(score_clean_text) else float(score_clean_text)

        # -------------------------------------------------
        # PRIORITY
        # LOWER = BETTER
        # -------------------------------------------------

        p_parenthetical = priority.get(tty_parenthetical, 99)
        p_clean_text = priority.get(tty_clean_text, 99)

        # =================================================
        # suffix_clean_text WINS
        # =================================================

        if (p_clean_text < p_parenthetical) or (p_clean_text == p_parenthetical and score_clean_text >= score_parenthetical):

            winner = suffix_clean_text
            parsed = row.get("clean_text")

            return pd.Series({

                out_cols[0]: row.get(f"rxnorm_match{winner}"),
                out_cols[1]: row.get(f"rxcui{winner}"),
                out_cols[2]: row.get(f"score{winner}"),
                out_cols[3]: row.get(f"sbdf{winner}"),
                out_cols[4]: row.get(f"tty{winner}"),
                "parsed": parsed
            })

        # =================================================
        # suffix_parenthetical_text WINS
        # =================================================

        elif (p_parenthetical < p_clean_text) or (p_parenthetical == p_clean_text and score_parenthetical > score_clean_text):

            winner = suffix_parenthetical_text
            parsed = row.get("parenthetical_text")

            return pd.Series({

                out_cols[0]: row.get(f"rxnorm_match{winner}"),
                out_cols[1]: row.get(f"rxcui{winner}"),
                out_cols[2]: row.get(f"score{winner}"),
                out_cols[3]: row.get(f"sbdf{winner}"),
                out_cols[4]: row.get(f"tty{winner}"),
                "parsed": parsed
            })

        # =================================================
        # FALLBACK
        # =================================================

        else:
            winner = suffix_clean_text
            parsed = row.get("clean_text")

            return pd.Series({
                out_cols[0]: row.get(f"rxnorm_match{winner}"),
                out_cols[1]: row.get(f"rxcui{winner}"),
                out_cols[2]: row.get(f"score{winner}"),
                out_cols[3]: row.get(f"sbdf{winner}"),
                out_cols[4]: row.get(f"tty{winner}"),
                "parsed": parsed
            })
    # -----------------------------------------------------
    # APPLY
    # -----------------------------------------------------

    results = df.apply(
        _select_best_match_row,
        axis=1
    )

    df[results.columns] = results

    # -----------------------------------------------------
    # CLEAN LIST FORMAT
    # -----------------------------------------------------

    df["parsed"] = df["parsed"].apply(
        _normalize_list_field
    )

    return df