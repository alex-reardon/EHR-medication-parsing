import re
import pandas as pd
import logging


def load_formulation_csv(path: str) -> str:
    """
    Load formulation dictionary and build unit regex pattern
    """
    form_df = pd.read_csv(path)
    form_df = form_df[form_df["category"] == "form"]

    form_df = form_df.sort_values(
    by="raw",
    key=lambda x: x.str.len(),
    ascending=False
    )

    return form_df 



def extract_amount_and_form(df: pd.DataFrame, input_col: str, output_col: str, forms_df: pd.DataFrame):
    """
    Extract amount + form and remove matched portion from text
    """

    amounts = []
    forms = []
    cleaned_texts = []

    for text in df[input_col]:

        # --- initialize per row (CRITICAL FIX) ---
        amount = None
        form = None

        if pd.isna(text):
            amounts.append(amount)
            forms.append(form)
            cleaned_texts.append(text)
            continue

        text = str(text).lower()

        # --- try matching ---
        for _, row in forms_df.iterrows():
            form_pattern = row["raw"]
            form_name = row["replacement"]

            pattern = rf'\b(?:(\d+(?:\.\d+)?|\.\d+)\s*)?{form_pattern}\b'
            match = re.search(pattern, text)

            if match:
                val = match.group(1)

                if val:
                    num = float(val)
                    amount = int(num) if num.is_integer() else num

                form = form_name

                # remove match
                text = re.sub(pattern, '', text)

                break  # stop after first match

        # --- cleanup ---
        text = re.sub(r'\s+', ' ', text).strip()

        # --- append ONCE per row (CRITICAL FIX) ---
        amounts.append(amount)
        forms.append(form)
        cleaned_texts.append(text)

    # --- final assignment ---
    assert len(amounts) == len(df), "Length mismatch: amounts"
    assert len(forms) == len(df), "Length mismatch: forms"
    assert len(cleaned_texts) == len(df), "Length mismatch: cleaned_texts"

    df["amount"] = amounts
    df["form"] = forms
    df[output_col] = cleaned_texts

    return df



def apply_extract_amount_and_form(df, input_col, output_col, path) : 
    forms_df = load_formulation_csv(path)
    df = extract_amount_and_form(df, input_col, output_col, forms_df)

    # Metrics
    mapped = df["form"].notna().sum()
    print(f"Form Frequency Extraction Complete: {mapped}/{len(df)} rows mapped ({mapped/len(df):.2%})")

    mapped = df["amount"].notna().sum()
    print(f"Amount Frequency Extraction Complete: {mapped}/{len(df)} rows mapped ({mapped/len(df):.2%})")

    return df 