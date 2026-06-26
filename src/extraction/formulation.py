import logging
import re
import pandas as pd

logger = logging.getLogger(__name__)

# ---------------------------------------------------------
# GLOBALS
# ---------------------------------------------------------
NUM = r'(?:\d+(?:\.\d+)?|\.\d+)'
SEP = r'\s*-\s*'

# ---------------------------------------------------------
# BUILD SINGLE REGEX FROM COMPILED RULES
# ---------------------------------------------------------

def _build_formulation_regex(compiled_rules):
    # Sort by length descending to ensure longer phrases match first
    raw_patterns = sorted(
        [rule["pattern_raw"] for rule in compiled_rules], 
        key=len, 
        reverse=True
    )
    form_pattern = "|".join(raw_patterns)

    NUM_SINGLE = rf'(?:{NUM})'
    NUM_RANGE = rf'(?:{NUM_SINGLE}(?:{SEP}{NUM_SINGLE})+)'

    # We use \b and order NUM_RANGE first so "1-2" matches fully before "1" does
    # Use a negative lookbehind to ensure we aren't mid-word, 
        # but don't use \b which chokes on "1tab"
    pattern = rf'''
        (?:
            (?<![a-zA-Z0-9]) # Ensure we aren't starting inside a word
            (?P<amount>{NUM_RANGE}|{NUM_SINGLE})
        )?
        \s*
        (?P<form>{form_pattern})
        \b
        '''
    return re.compile(
        pattern,
        flags=re.IGNORECASE | re.VERBOSE
    )


# ---------------------------------------------------------
# PARSE SINGLE TEXT
# ---------------------------------------------------------
def extract_formulations(text, compiled_pattern, compiled_rules):
    parsed = {"forms": [], "clean_text": text}

    if pd.isna(text) or text == "":
        return parsed

    working = str(text)
    matches = list(compiled_pattern.finditer(working))

    if not matches:
        parsed["clean_text"] = working.strip()
        return parsed

    for match in matches:
        amount_raw = match.group('amount')
        form_raw = match.group('form').lower()
        
        mapped_form = form_raw
        for rule in compiled_rules:
            if rule["pattern"].fullmatch(form_raw):
                mapped_form = rule["replacement"]
                break

        # Normalize Amount
        normalized_amount = None
        if amount_raw:
            amount_raw = amount_raw.strip()
            
            # Check for range/ratio
            if re.search(r'[-]', amount_raw):
                parts = re.split(SEP, amount_raw)
                normalized_amount = []
                for p in parts:
                    try:
                        val = float(p)
                        normalized_amount.append(int(val) if val.is_integer() else val)
                    except ValueError:
                        normalized_amount.append(p)
            else:
                try:
                    val = float(amount_raw)
                    normalized_amount = int(val) if val.is_integer() else val
                except ValueError:
                    normalized_amount = amount_raw

        parsed["forms"].append({
            "form": mapped_form,
            "amount": normalized_amount,
            "raw": match.group(0).strip()
        })

    # Clean text: remove matches and collapse extra whitespace
    working = compiled_pattern.sub(" ", working)
    working = re.sub(r'\s+', ' ', working).strip()
    parsed["clean_text"] = working

    return parsed



# ---------------------------------------------------------
# APPLY TO DATAFRAME
# ---------------------------------------------------------
def apply_formulation_extraction(df, compiled_rules):
    df = df.copy()
    compiled_pattern = _build_formulation_regex(compiled_rules)

    # 1. Generate full parsed column
    df["parsed_formulations"] = df["clean_text"].apply(
        lambda x: extract_formulations(x, compiled_pattern, compiled_rules)
    )

    # 2. Extract Forms (Unique & Non-Null)
    df["form"] = df["parsed_formulations"].apply(
        lambda x: list(dict.fromkeys([f["form"] for f in x["forms"] if f["form"]])) 
        if x["forms"] else None
    )

    # 3. Flatten Amounts (Unique & Non-Null)
    def flatten_amounts(forms):
        amounts = []
        for f in forms:
            amt = f["amount"]
            if amt is None: continue
            if isinstance(amt, list):
                amounts.extend(amt)
            else:
                amounts.append(amt)
        return list(dict.fromkeys(amounts)) if amounts else None

    df["amount"] = df["parsed_formulations"].apply(
        lambda x: flatten_amounts(x["forms"]) if x["forms"] else None
    )

    # 4. Update Clean Text
    df["clean_text"] = df["parsed_formulations"].apply(lambda x: x["clean_text"])

    # Metrics
    mapped_forms = df["form"].notna().sum()
    mapped_amounts = df["amount"].notna().sum()
    logger.info("Form Extraction: %d/%d (%.1f%%)", mapped_forms, len(df), 100 * mapped_forms / len(df))
    logger.info("Amount Extraction: %d/%d (%.1f%%)", mapped_amounts, len(df), 100 * mapped_amounts / len(df))

    return df