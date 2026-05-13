import re
import pandas as pd


def load_formulation_csv(path: str):
    form_df = pd.read_csv(path)
    form_df = form_df[form_df["category"] == "form"]

    form_df = form_df.sort_values(
        by="raw",
        key=lambda x: x.str.len(),
        ascending=False
    )

    return form_df


def extract_amount_and_form(df: pd.DataFrame, input_col: str, output_col: str, forms_df: pd.DataFrame):

    all_amounts = []
    all_forms = []
    cleaned_texts = []

    for text in df[input_col]:

        amounts = []
        forms = []

        if pd.isna(text):
            all_amounts.append(None)
            all_forms.append(None)
            cleaned_texts.append(text)
            continue

        text = str(text).lower()

        # -------------------------------
        # LOOP THROUGH ALL FORM PATTERNS
        # -------------------------------
        for _, row in forms_df.iterrows():
            form_pattern = row["raw"]
            form_name = row["replacement"]

            pattern = rf'\b(?:(\d+(?:\.\d+)?|\.\d+)\s*)?{form_pattern}\b'

            matches = list(re.finditer(pattern, text))

            if not matches:
                continue

            for match in matches:
                val = match.group(1)

                if val:
                    num = float(val)
                    num = int(num) if num.is_integer() else num
                    amounts.append(num)

                forms.append(form_name)

            # remove ALL matches for this pattern
            text = re.sub(pattern, '', text)

        # -------------------------------
        # CLEANUP
        # -------------------------------
        text = re.sub(r'\s+', ' ', text).strip()

        # deduplicate
        forms = list(dict.fromkeys(forms)) if forms else None
        amounts = list(dict.fromkeys(amounts)) if amounts else None

        all_amounts.append(amounts)
        all_forms.append(forms)
        cleaned_texts.append(text)

    # -------------------------------
    # FINAL ASSIGNMENT
    # -------------------------------
    df["amount"] = all_amounts
    df["form"] = all_forms
    df[output_col] = cleaned_texts

    return df


def apply_extract_amount_and_form(df, input_col, output_col, path):
    forms_df = load_formulation_csv(path)
    df = extract_amount_and_form(df, input_col, output_col, forms_df)
    df[output_col] = df[output_col].str.replace(r'\s*/\s*', '/', regex=True)

    mapped = df["form"].notna().sum()
    print(f"Form Extraction Complete: {mapped}/{len(df)} rows mapped ({mapped/len(df):.2%})")

    mapped = df["amount"].notna().sum()
    print(f"Amount Extraction Complete: {mapped}/{len(df)} rows mapped ({mapped/len(df):.2%})")

    return df