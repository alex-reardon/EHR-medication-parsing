import re
import pandas as pd
import logging



import pandas as pd
import re

num_words = {
    1: "one", 2: "two", 3: "three", 4: "four",
    5: "five", 6: "six", 7: "seven", 8: "eight",
    9: "nine", 10: "ten", 11: "eleven", 12: "twelve"
}

time_units = {
    "day": r"(?:d|day|daily|days|24\s*(?:hours?|hrs?|h))",
    "week": r"(?:w|week|wk|wks|weeks|weekly)",
    "month": r"(?:m|mo|month|months|monthly)",
    "year": r"(?:y|yr|year|yearly|annually)",
    "hour": r"(?:h|hr|hour|hours|hrs)"
}

rows = []

for n, word in num_words.items():
    for unit_name, unit_pattern in time_units.items():

        # -------------------------------
        # Pattern 1: "2x per day", "two daily"
        # -------------------------------

        pattern_standard = re.sub(r"\s+", "", rf"""
        \b
        (?:{n}(?:\.0+)?|{word})
        \s*
        (?:(?:x|times?)\s*)?
        (?:/\s*|same\s*|each\s*|every\s*|per\s*|a\s*)?
        {unit_pattern}
        \b
        """)

        rows.append({
            "raw": pattern_standard,
            "replacement": f"{n}x/{unit_name}",
            "category": "freq",
            "notes": f"{n} per {unit_name}"
        })

        # -------------------------------
        # Pattern 2: "q2w", "q3d"
        # -------------------------------
        pattern_q = re.sub(r"\s+", "", rf"""
        \b
        q\s*(?:{n}(?:\.0+)?|{word})
        \s*
        {unit_pattern}
        \b
        """)

        rows.append({
            "raw": pattern_q,
            "replacement": f"q{n} {unit_name}",
            "category": "freq",
            "notes": f"q{n} {unit_name}"
        })


for n, word in num_words.items():
    for unit_name, unit_pattern in time_units.items():

        pattern_every = re.sub(r"\s+", "", rf"""
        \b
        every\s*(?:{n}(?:\.0+)?|{word})
        \s*
        {unit_pattern}
        \b
        """)

        rows.append({
            "raw": pattern_every,
            "replacement": f"q{n} {unit_name}",
            "category": "freq",
            "notes": f"every {n} {unit_name}"
        })




for n, word in num_words.items():
    for unit_name, unit_pattern in time_units.items():

        pattern_days_per_week = re.sub(r"\s+", "", rf"""
        \b
        (?:{n}(?:\.0+)?|{word})
        \s*
        (?:d|day|days)
        \s*
        (?:/\s*|per\s*|a\s*)
        \s*
        (?:w|week|weeks|wk|m|mo|month|months)
        \b
        """)

        rows.append({
            "raw": pattern_days_per_week,
            "replacement": f"{n}x/{unit_name}",
            "category": "freq",
            "notes": f"{n} per {unit_name}"
        })


## Capture once and twice 
special_words = {
    "once": 1,
    "twice": 2
}

for word, n in special_words.items():
    for unit_name, unit_pattern in time_units.items():

        pattern = rf"\b{word}\s*(?:/\s*|same\s*each\s*|every\s*|per\s*|a\s*)?{unit_pattern}\b"

        rows.append({
            "raw": pattern,
            "replacement": f"{n}x/{unit_name}",
            "category": "freq",
            "notes": f"{word} per {unit_name}"
        })


## stand alone once 
rows.append({
    "raw": r"\bonce\b",
    "replacement": "1x",
    "category": "freq",
    "notes": "once (no unit)"
})

# stand alone twice
rows.append({
    "raw": r"\btwice\b",
    "replacement": "2x",
    "category": "freq",
    "notes": "twice (no unit)"
})



df = pd.DataFrame(rows)
df_norm = pd.read_csv("/Users/emudr/PPMI_LEDD/data/normalization_dictionary.csv")
df_combined = pd.concat([df_norm, df], ignore_index=True)
df_combined = df_combined.drop_duplicates(subset=["raw", "replacement"])
df_combined = df_combined.sort_values(by=["category", "replacement"])
df_combined.to_csv("/Users/emudr/PPMI_LEDD/data/normalization_dictionary_updated.csv", index=False)