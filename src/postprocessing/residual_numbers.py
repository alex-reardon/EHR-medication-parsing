# postprocessing/residual_number_extraction.py
import logging
import re
import pandas as pd

logger = logging.getLogger(__name__)


# ---------------------------------------------------------
# EXTRACT RESIDUAL / UNMAPPED NUMBERS
# ---------------------------------------------------------

NUMBER_PATTERN = r'\b-?\d+(?:\.\d+)?\b'

# ---------------------------------------------------------
# EXTRACT RESIDUAL / NOISE TOKENS
# ---------------------------------------------------------
# Add/remove tokens here as you find new noise patterns.
# These are matched as WHOLE WORDS (case-insensitive) and
# pulled out into residual_tokens, not just discarded.

NOISE_WORDS = [
    "x", "xs", "times", "time", "q"
]
_NOISE_ALT = '|'.join(re.escape(w) for w in NOISE_WORDS)

# -----------------------------------------------------------------
# COMPOUND NUMBER+NOISE PATTERNS — must run BEFORE plain number strip
# Catches: x5, 1x5, 5times, .6h, 5x, 4xs, 0.6h, etc.
# Form A: noise-word/letter directly attached BEFORE a number  -> x5, x1.5
# Form B: number directly attached BEFORE a noise-word/letter  -> 5x, 5times, .6h
# -----------------------------------------------------------------
COMPOUND_PATTERN = re.compile(
    rf'''
    \b
    (?:
        (?:{_NOISE_ALT})\d+(?:\.\d+)?      # x5, x1.5
        |
        \d+(?:\.\d+)?(?:{_NOISE_ALT})      # 5x, 5times, .6h  (note: \d+ also matches ".6" via leading optional digit below)
    )
    \b
    |
    \.\d+(?:{_NOISE_ALT})                   # .6h  (leading-dot decimals with no integer part)
    ''',
    flags=re.I | re.X
)

# standalone noise words (no digits attached) — second pass
NOISE_PATTERN = re.compile(rf'\b(?:{_NOISE_ALT})\b', flags=re.I)

# any leftover single alpha character
SINGLE_CHAR_PATTERN = re.compile(r'\b[a-zA-Z]\b')


def _extract_residual_numbers(text):

    """
    Extract leftover standalone numbers and noise tokens that
    were not captured during dose extraction.

    Examples
    --------
    aspirin 81
        -> residual_numbers = [81]

    morphine -1
        -> residual_numbers = [-1]

    trazodone 0.5
        -> residual_numbers = [0.5]

    carbidopa levodopa qds
        -> residual_tokens = ["qds"]

    carbidopa/levodopa x5
        -> residual_tokens = ["x5"]

    carbidopa levodopa 1x5
        -> residual_tokens = ["1x5"]

    carbidopa levodopa 5times
        -> residual_tokens = ["5times"]

    carbidopa levodopa .6h
        -> residual_tokens = [".6h"]
    """

    if pd.isna(text):
        return {
            "residual_numbers": None,
            "residual_tokens": None,
            "clean_text": text
        }

    working = str(text)

    # -----------------------------------------------------
    # PASS 1: COMPOUND NUMBER+NOISE TOKENS (x5, 5times, .6h, 1x5, ...)
    # must run FIRST, before numbers or noise words are stripped
    # individually, or the attachment context is lost
    # -----------------------------------------------------

    compound_matches = re.findall(COMPOUND_PATTERN, working)
    # re.findall with a non-grouped pattern returns full matches as strings
    # (no capturing groups used above, so this is safe)

    working = re.sub(
        COMPOUND_PATTERN,
        ' ',
        working
    )

    # -----------------------------------------------------
    # PASS 2: PLAIN STANDALONE NUMBERS
    # -----------------------------------------------------

    number_matches = re.findall(
        NUMBER_PATTERN,
        working
    )

    parsed_numbers = []

    for m in number_matches:

        try:

            val = float(m)

            parsed_numbers.append(
                int(val)
                if val.is_integer()
                else val
            )

        except ValueError:

            parsed_numbers.append(m)

    working = re.sub(
        NUMBER_PATTERN,
        ' ',
        working
    )

    # -----------------------------------------------------
    # REMOVE LEFTOVER HYPHENS
    # -----------------------------------------------------

    working = re.sub(
        r'\s*-\s*',
        ' ',
        working
    )

    # -----------------------------------------------------
    # PASS 3: STANDALONE NOISE WORDS (no digits attached)
    # -----------------------------------------------------

    noise_word_matches = [m.lower() for m in re.findall(NOISE_PATTERN, working)]

    working = re.sub(
        NOISE_PATTERN,
        ' ',
        working
    )

    # -----------------------------------------------------
    # PASS 4: LEFTOVER STANDALONE SINGLE CHARACTERS
    # -----------------------------------------------------

    single_char_matches = re.findall(SINGLE_CHAR_PATTERN, working)

    working = re.sub(
        SINGLE_CHAR_PATTERN,
        ' ',
        working
    )

    residual_tokens = (
        [m.lower() for m in compound_matches]
        + noise_word_matches
        + single_char_matches
    )

    # -----------------------------------------------------
    # COLLAPSE WHITESPACE
    # -----------------------------------------------------

    working = re.sub(
        r'\s+',
        ' ',
        working
    ).strip()

    return {

        "residual_numbers":
            parsed_numbers
            if parsed_numbers
            else None,

        "residual_tokens":
            residual_tokens
            if residual_tokens
            else None,

        "clean_text":
            working
    }


# ---------------------------------------------------------
# WRAPPER
# ---------------------------------------------------------

def apply_residual_number_extraction(
    df,
    text_col="clean_text"
):

    df = df.copy()

    parsed = df[text_col].apply(
        _extract_residual_numbers
    )

    df["residual_numbers"] = parsed.apply(
        lambda x: x["residual_numbers"]
    )

    df["residual_tokens"] = parsed.apply(
        lambda x: x["residual_tokens"]
    )

    df[text_col] = parsed.apply(
        lambda x: x["clean_text"]
    )

    mapped = df["residual_numbers"].notna().sum()
    tokens_found = df["residual_tokens"].notna().sum()

    logger.info(
        "Residual Number Extraction: %d/%d (%.1f%%)",
        mapped, len(df), 100 * mapped / len(df)
    )
    logger.info(
        "Residual Token Extraction: %d/%d (%.1f%%)",
        tokens_found, len(df), 100 * tokens_found / len(df)
    )

    return df