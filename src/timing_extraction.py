def extract_weekday_frequency(text):
    if pd.isna(text):
        return None

    text = str(text).lower()

    patterns = [
        r"\bmon(?:day)?\b",
        r"\btue(?:s|sday)?\b",
        r"\bwed(?:nesday)?\b",
        r"\bthu(?:rs|rsday)?\b",
        r"\bfri(?:day)?\b",
        r"\bsat(?:urday)?\b",
        r"\bsun(?:day)?\b",
    ]

    found = set()

    for pattern in patterns:
        matches = re.findall(pattern, text)
        if matches:
            found.add(pattern)  # avoids double counting

    count = len(found)

    return f"{count}x/week" if count > 0 else None




def apply_weekday_frequency(df):
    mask = df["frequency_per_day"].isna() # FIXME

    df.loc[mask, "frequency_per_day"] = df.loc[mask, "clean_text"].apply(
        extract_weekday_frequency
    )

    return df




def build_timing_pattern_from_df(df):
    grouped = df_to_grouped_dict(df)

    patterns = {}

    for label, terms in grouped.items():
        processed_terms = []

        for term in terms:
            term = str(term).lower().strip()
            
            # remove any existing \b to prevent double wrapping
            term = term.replace(r"\b", "")

            processed_terms.append(term)

        pattern_str = r"\b(?:{})\b".format("|".join(processed_terms))

        patterns[label] = re.compile(pattern_str)

    return patterns



def extract_timing_frequency(text: str, timing_patterns: dict) -> int:
    if pd.isna(text):
        return None

    text = str(text).lower()

    matches = set()

    for label, pattern in timing_patterns.items():
        if pattern.search(text):
            matches.add(label)

    if len(matches) == 0:
        return None

    return len(matches)




def apply_timing_extraction(df, timing_patterns):
    df["freq_timing"] = df["clean_text"].apply(
        lambda x: extract_timing_frequency(x, timing_patterns)
    )
    return df




def remove_timing_terms(text, timing_patterns):
    if pd.isna(text):
        return text

    text = str(text).lower()

    for pattern in timing_patterns.values():
        text = pattern.sub("", text)

    text = re.sub(r"\s+", " ", text).strip()

    return text



  # -------------------------------
    # WEEKDAY fallback
    # -------------------------------
    df = apply_weekday_frequency(df)

    df["freq_raw"] = df["frequency_per_day"].apply(clean_numeric_freq)



   # PASS 3: timing extraction
    # -------------------------------
    timing_df = load_frequency_rules(path, category = "time_of_day", use_priority = False)
    timing_patterns = build_timing_pattern_from_df(timing_df)

    df = apply_timing_extraction(
        df,
        timing_patterns=timing_patterns
    )

    df["clean_text"] = df["clean_text"].apply(
    lambda x: remove_timing_terms(x, timing_patterns)
)


    # -------------------------------
    # PASS 4: resolve final frequency
    # -------------------------------
    df["freq_raw"] = df.apply(
        lambda row: resolve_frequency(
            row["freq_raw"],
            row["freq_timing"]
        ),
        axis=1
    )


    
def resolve_frequency(numeric_freq, timing_freq):
    
    # numeric always wins
    if pd.notna(numeric_freq):
        return numeric_freq

    # fallback to timing
    if pd.notna(timing_freq):
        return timing_freq

    return None