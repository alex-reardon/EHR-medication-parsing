import re
import pandas as pd
import logging


num_words = {
    1: "one", 2: "two", 3: "three", 4: "four",
    5: "five", 6: "six", 7: "seven", 8: "eight",
    9: "nine", 10: "ten", 11: "eleven", 12: "twelve"
}

time_units = {
    "day": r"(?:d|day|daily|day|24\s*(?:hours?|hrs?|h))",
    "week": r"(?:w|week|wk|wks|weeks|weekly)",
    "month": r"(?:m|mo|month|months|monthly)",
    "year": r"(?:y|yr|year|yearly|annually)",
    "hour": r"(?:h|hr|hour|hours|hrs)"
}


n_per_day = {
    "day" : 1, 
    "week" : 7, 
    "month" : 30
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

        # Translate to per day
        if unit_name in n_per_day:
            replacement = n / n_per_day[unit_name]
        else:
            replacement = f"{n}x/{unit_name}"

        rows.append({
            "raw": pattern_standard,
            "replacement": replacement,
            "priority": 1,
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

        # ✅ NEW LOGIC (interval-based)
        if unit_name in n_per_day:
            replacement = 1 / (n * n_per_day[unit_name])
        else:
            replacement = f"q{n} {unit_name}"

        rows.append({
            "raw": pattern_q,
            "replacement": replacement,
            "priority": 1,
            "notes": f"q {n} {unit_name}"
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

        # ✅ NEW LOGIC (interval-based)
        if unit_name in n_per_day:
            replacement = 1 / (n * n_per_day[unit_name])
        else:
            replacement = f"q{n} {unit_name}"

        rows.append({
            "raw": pattern_every,
            "replacement": replacement,
            "priority": 1,
            "notes": f"every {n} {unit_name}"
        })



for n, word in num_words.items():
    time_units_no_day = {
    "week": r"(?:w|week|wk|wks|weeks|weekly)",
    "month": r"(?:m|mo|month|months|monthly)",
    "year": r"(?:y|yr|year|yearly|annually)",
    "hour": r"(?:h|hr|hour|hours|hrs)"}
    for unit_name, unit_pattern in time_units_no_day.items():

        pattern_days_per_week = re.sub(r"\s+", "", rf"""
        \b
        (?:{n}(?:\.0+)?|{word})
        \s*
        (?:d|day|days)
        \s*
        (?:/\s*|per\s*|a\s*|each\s*|in\s*)?
        \s*
        {unit_pattern}
        \b
        """)

      
        # ✅ NEW LOGIC
        if unit_name in n_per_day:
            replacement = n / n_per_day[unit_name]
        else:
            replacement = f"{n}x/{unit_name}"

        rows.append({
            "raw": pattern_days_per_week,
            "replacement": replacement,
            "priority": 1,
            "notes": f"{n} days per {unit_name}"
        })

## Capture once and twice 
special_words = {
    "once": 1,
    "twice": 2
}

for word, n in special_words.items():
    for unit_name, unit_pattern in time_units.items():

        pattern = rf"\b{word}\s*(?:/\s*|same\s*each\s*|every\s*|per\s*|a\s*)?{unit_pattern}\b"

        # ✅ NEW LOGIC
        if unit_name in n_per_day:
            replacement = n / n_per_day[unit_name]
        else:
            replacement = f"{n}x/{unit_name}"

        rows.append({
            "raw": pattern,
            "replacement": replacement,
            "priority": 1,
            "notes": f"{word} per {unit_name}"
        })


## stand alone once 
rows.append({
    "raw": r"\bonce\b",
    "replacement": "1x",
    "priority": 1,
    "notes": "once (no unit)"
})

# stand alone twice
rows.append({
    "raw": r"\btwice\b",
    "replacement": "2x",
    "priority": 1,
    "notes": "twice (no unit)"
})



df = pd.DataFrame(rows)
df['category'] = "frequency"
df_norm = pd.read_csv("/Users/emudr/PPMI_LEDD/data/frequency_dictionary_manual.csv")
df_combined = pd.concat([df_norm, df], ignore_index=True)
df_combined = df_combined.drop_duplicates(subset=["raw", "replacement"])
df_combined = df_combined.sort_values(by=["priority", "replacement"])
df_combined.to_csv("/Users/emudr/PPMI_LEDD/data/frequency_dictionary.csv", index=False)