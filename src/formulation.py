import re
import pandas as pd


# ---------------------------------------------------------
# LOAD FORMULATION RULES
# ---------------------------------------------------------
def load_formulation_csv(path: str):

    forms_df = pd.read_csv(path)

    forms_df = forms_df[
        forms_df["category"] == "form"
    ].copy()

    forms_df["raw"] = (
        forms_df["raw"]
        .astype(str)
        .str.strip()
    )

    forms_df["replacement"] = (
        forms_df["replacement"]
        .astype(str)
        .str.lower()
        .str.strip()
    )

    # longest regex first
    forms_df = forms_df.sort_values(
        by="raw",
        key=lambda x: x.str.len(),
        ascending=False
    )

    return forms_df


# ---------------------------------------------------------
# BUILD SINGLE REGEX
# IMPORTANT:
# raw column ALREADY contains regex
# ---------------------------------------------------------
def build_form_regex(forms_df):

    form_pattern = "|".join(
        forms_df["raw"]
        .dropna()
        .tolist()
    )

    # optional amount before formulation
    pattern = (
        rf'(?:(\d+(?:\.\d+)?|\.\d+)\s*)?'
        rf'({form_pattern})'
    )

    return re.compile(
        pattern,
        flags=re.IGNORECASE
    )


# ---------------------------------------------------------
# PARSE SINGLE TEXT
# ---------------------------------------------------------
def parse_formulations(
    text,
    compiled_pattern,
    form_map
):

    parsed = {
        "forms": [],
        "clean_text": text
    }

    if pd.isna(text):
        return parsed

    working = str(text)

    # -----------------------------------------------------
    # find all matches
    # -----------------------------------------------------
    matches = list(
        compiled_pattern.finditer(working)
    )

    # -----------------------------------------------------
    # no matches
    # -----------------------------------------------------
    if not matches:

        parsed["clean_text"] = working.lower()

        return parsed

    # -----------------------------------------------------
    # extract semantic entities
    # -----------------------------------------------------
    for match in matches:

        amount = match.group(1)

        raw_form = match.group(2)

        raw_form_lower = raw_form.lower()

        # -------------------------------------------------
        # map regex pattern -> canonical form
        # -------------------------------------------------
        mapped_form = None

        for pattern, replacement in form_map.items():

            if re.fullmatch(
                pattern,
                raw_form_lower,
                flags=re.IGNORECASE
            ):

                mapped_form = replacement
                break

        if mapped_form is None:
            mapped_form = raw_form_lower

        # -------------------------------------------------
        # normalize amount
        # -------------------------------------------------
        if amount:

            amount = float(amount)

            if amount.is_integer():
                amount = int(amount)

        parsed["forms"].append({
            "form": mapped_form,
            "amount": amount
        })

    # -----------------------------------------------------
    # remove matched spans
    # NON-DESTRUCTIVE
    # -----------------------------------------------------
    working = compiled_pattern.sub(" ", working)

    # -----------------------------------------------------
    # cleanup
    # -----------------------------------------------------
    working = working.lower()

    working = re.sub(
        r"\s+",
        " ",
        working
    ).strip()

    parsed["clean_text"] = working

    return parsed


# ---------------------------------------------------------
# APPLY TO DATAFRAME
# ---------------------------------------------------------
def apply_extract_amount_and_form(
    df,
    path
):

    # -----------------------------------------------------
    # load formulation rules
    # -----------------------------------------------------
    forms_df = load_formulation_csv(path)

    # -----------------------------------------------------
    # build regex map
    # -----------------------------------------------------
    form_map = dict(
        zip(
            forms_df["raw"],
            forms_df["replacement"]
        )
    )

    # -----------------------------------------------------
    # compile ONE regex
    # -----------------------------------------------------
    compiled_pattern = build_form_regex(forms_df)

    # -----------------------------------------------------
    # parse formulations
    # -----------------------------------------------------
    df["parsed_formulations"] = df["clean_text"].apply(
        lambda x: parse_formulations(
            x,
            compiled_pattern,
            form_map
        )
    )

    # -----------------------------------------------------
    # flatten forms
    # -----------------------------------------------------
    df["form"] = df["parsed_formulations"].apply(
        lambda x:
            list(dict.fromkeys([
                f["form"]
                for f in x["forms"]
                if f["form"] is not None
            ]))
            if x["forms"]
            else None
    )

    # -----------------------------------------------------
    # flatten amounts
    # -----------------------------------------------------
    df["amount"] = df["parsed_formulations"].apply(
        lambda x:
            list(dict.fromkeys([
                f["amount"]
                for f in x["forms"]
                if f["amount"] is not None
            ]))
            if x["forms"]
            else None
    )

    # -----------------------------------------------------
    # clean text without forms
    # -----------------------------------------------------
    df["clean_text"] = df["parsed_formulations"].apply(
        lambda x: x["clean_text"]
    )

    # -----------------------------------------------------
    # cleanup output text
    # -----------------------------------------------------
    df["clean_text"] = (
        df["clean_text"]
        .str.replace(r'\s*/\s*', '/', regex=True)
        .str.replace(r'\s+', ' ', regex=True)
        .str.strip()
    )

    # -----------------------------------------------------
    # metrics
    # -----------------------------------------------------
    mapped_forms = df["form"].notna().sum()

    print(
        f"Form Extraction Complete: "
        f"{mapped_forms}/{len(df)} "
        f"({mapped_forms/len(df):.2%})"
    )

    mapped_amounts = df["amount"].notna().sum()

    print(
        f"Amount Extraction Complete: "
        f"{mapped_amounts}/{len(df)} "
        f"({mapped_amounts/len(df):.2%})"
    )

    return df