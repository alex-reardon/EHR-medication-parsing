import re
import pandas as pd
import logging
from functools import lru_cache
import numpy as np

logger = logging.getLogger(__name__)


# =========================================================
# HELPERS
# =========================================================
def _has_valid_existing_value(val):

    if val is None:
        return False

    if isinstance(val, float) and pd.isna(val):
        return False

    if isinstance(val, list) and len(val) == 0:
        return False

    return True


# =========================================================
# CORE FAST EXTRACTOR (CACHED)
# =========================================================
def _build_frequency_regex(compiled_rules):

    compiled_rules = sorted(
    compiled_rules,
    key=lambda x: len(x["pattern_raw"]),
    reverse=True
    )

    @lru_cache(maxsize=20000)
    def _extract_frequency_from_text(text):

        if text is None or (
            isinstance(text, float)
            and pd.isna(text)
        ):
            return None, None, text

        text = str(text).lower()

        cleaned = text

        matches = []

        raw_matches = []

        # -------------------------------------------------
        # APPLY RULES
        # -------------------------------------------------
        for rule in compiled_rules:

            pattern = rule["pattern"]

            replacement = rule["replacement"]

            found = list(
                pattern.finditer(cleaned)
            )

            if not found:
                continue

            # ---------------------------------------------
            # STORE NORMALIZED MATCH
            # ---------------------------------------------
            matches.append(replacement)

            # ---------------------------------------------
            # STORE RAW MATCHES
            # ---------------------------------------------
            raw_matches.extend([
                m.group(0)
                for m in found
            ])

            # ---------------------------------------------
            # REMOVE MATCHES
            # ---------------------------------------------
            cleaned = pattern.sub(
                " ",
                cleaned
            )

        # -------------------------------------------------
        # CLEANUP
        # -------------------------------------------------
        if matches:

            matches = list(
                dict.fromkeys(matches)
            )

            raw_matches = list(
                dict.fromkeys(raw_matches)
            )

            cleaned = re.sub(
                r"\s+",
                " ",
                cleaned
            ).strip()

            return (
                matches,
                raw_matches,
                cleaned
            )

        return (
            None,
            None,
            text
        )

    return _extract_frequency_from_text


# =========================================================
# APPLY FREQUENCY EXTRACTION
# =========================================================
def extract_frequency_fast(
    df: pd.DataFrame,
    compiled_rules,
    freq_col="frequency_per_day",
    raw_col="frequency_raw"
):

    df = df.copy()

    # -----------------------------------------------------
    # ENSURE COLS EXIST
    # -----------------------------------------------------
    if freq_col not in df.columns:
        df[freq_col] = None

    if raw_col not in df.columns:
        df[raw_col] = None

    extractor = _build_frequency_regex(
        compiled_rules
    )

    # -----------------------------------------------------
    # PROCESS ROW
    # -----------------------------------------------------
    def _process_frequency_row(row):

        text = row["clean_text"]

        existing = row[freq_col]

        existing_raw = row[raw_col]

        new_matches, raw_matches, cleaned = extractor(
            text
        )

        # -------------------------------------------------
        # NOTHING NEW FOUND
        # -------------------------------------------------
        if not new_matches:

            return pd.Series([
                existing,
                existing_raw,
                text
            ])

        # -------------------------------------------------
        # NORMALIZED MATCHES
        # -------------------------------------------------
        if _has_valid_existing_value(existing):

            existing = (
                existing
                if isinstance(existing, list)
                else [existing]
            )

            combined = list(
                dict.fromkeys(
                    existing + new_matches
                )
            )

        else:
            combined = new_matches

        # -------------------------------------------------
        # RAW MATCHES
        # -------------------------------------------------
        if _has_valid_existing_value(existing_raw):

            existing_raw = (
                existing_raw
                if isinstance(existing_raw, list)
                else [existing_raw]
            )

            combined_raw = list(
                dict.fromkeys(
                    existing_raw + raw_matches
                )
            )

        else:
            combined_raw = raw_matches

        return pd.Series([
            combined,
            combined_raw,
            cleaned
        ])

    # -----------------------------------------------------
    # APPLY
    # -----------------------------------------------------
    df[[freq_col, raw_col, "clean_text"]] = df.apply(
        _process_frequency_row,
        axis=1
    )

    # -----------------------------------------------------
    # CLEANUP
    # -----------------------------------------------------
    df["clean_text"] = (
        df["clean_text"]
        .str.replace(
            r"/\s*$",
            "",
            regex=True
        )
        .str.strip()
    )

    return df


# =========================================================
# NORMALIZE FREQUENCY
# =========================================================
def normalize_frequency_value(val):

    if isinstance(val, list):
        val = val[0] if val else None

    if isinstance(val, str):

        try:
            return float(val)

        except (ValueError, TypeError):
            return val

    return val


# =========================================================
# CLEAN NUMERIC FREQUENCY
# =========================================================
def normalize_numeric_frequency(numeric_freq):

    # -----------------------------------------------------
    # LIST INPUT
    # -----------------------------------------------------
    if isinstance(
        numeric_freq,
        (list, tuple, np.ndarray)
    ):

        if len(numeric_freq) == 0:
            return None

        cleaned = []

        for val in numeric_freq:

            if pd.isna(val):
                continue

            try:
                cleaned.append(
                    float(val)
                )

            except (ValueError, TypeError):
                continue

        if not cleaned:
            return None

        cleaned = list(
            set(cleaned)
        )

        return max(cleaned)

    # -----------------------------------------------------
    # SCALAR INPUT
    # -----------------------------------------------------
    if pd.isna(numeric_freq):
        return None

    try:
        return float(numeric_freq)

    except (ValueError, TypeError):
        return None


# =========================================================
# MAIN PIPELINE
# =========================================================
def apply_frequency_extraction(
    df: pd.DataFrame,
    compiled_rules
) -> pd.DataFrame:

    df = df.copy()

    # -----------------------------------------------------
    # PASS 1
    # EXPLICIT
    # -----------------------------------------------------
    df = extract_frequency_fast(
        df=df,
        compiled_rules=compiled_rules[
            "frequency_primary"
        ]
    )

    # -----------------------------------------------------
    # PASS 2
    # GENERAL
    # -----------------------------------------------------
    df = extract_frequency_fast(
        df=df,
        compiled_rules=compiled_rules[
            "frequency_secondary"
        ]
    )

    # -----------------------------------------------------
    # CLEAN NUMERIC
    # -----------------------------------------------------
    df["frequency_per_day"] = (
        df["frequency_per_day"]
        .apply(normalize_numeric_frequency)
        .apply(normalize_frequency_value)
    )

    # -----------------------------------------------------
    # CLEANUP
    # -----------------------------------------------------
    df["clean_text"] = (
        df["clean_text"]
        .str.replace(
            r'\s*/\s*',
            '/',
            regex=True
        )
    )

    # -----------------------------------------------------
    # METRICS
    # -----------------------------------------------------
    mapped = df[
        "frequency_per_day"
    ].notna().sum()

    logger.info(
        "Frequency Extraction Complete: %d/%d rows mapped (%.2f%%)",
        mapped, len(df), 100 * mapped / len(df)
    )

    return df