import re
import pandas as pd
import logging


num_words = {
    1: "one", 2: "two", 3: "three", 4: "four",
    5: "five", 6: "six", 7: "seven", 8: "eight",
    9: "nine", 10: "ten", 11: "eleven", 12: "twelve"
}

time_units = {
    "day": r"(?:24\s*(?:hours?|hrs?|h)|daily|days|day|d)",
    "week": r"(?:weekly|weeks|week|wks|wk|w)",
    "month": r"(?:monthly|months|month|mo|m)",
    "year": r"(?:annually|yearly|year|yr|y)",
    "hour": r"(?:hours|hour|hrs|hr|h)"
}

adverb_units = r"""
    (?:
        daily
        |weekly
        |monthly
        |yearly
        |annually
    )
"""

adverb_units = {

    "day": {
        "pattern": r"(?:daily)",
        "days": 1
    },

    "week": {
        "pattern": r"(?:weekly)",
        "days": 7
    },

    "month": {
        "pattern": r"(?:monthly)",
        "days": 30
    },

    "year": {
        "pattern": r"(?:yearly|annually)",
        "days": 365
    },

    "hour": {
        "pattern": r"(?:hourly)",
        "days": 1/24
    }
}


n_per_day = {
    "day" : 1, 
    "week" : 7, 
    "month" : 30,
    "year" : 365, 
    "hour" : 24

}


n_per_day_adverb = {
    "daily" : 1, 
    "weekly" : 7, 
    "monthly" : 30,
    "yearly" : 365,
    "annually" : 365,
    "hourly" : 1/24

}


rows = []

for n, word in num_words.items():
    for unit_name, unit_pattern in time_units.items():

        # -------------------------------
        # Pattern 1: "2x per day"
        # -------------------------------

        pattern_standard = re.sub(r"\s+", "", rf"""
            \b
            (?:{n}(?:\.0+)?|{word})
            \s*
            (?:
                (?:(?:x|times?)\s*)?
                (?:/\s*|same\s*|each\s*|every\s*|per\s*|a\s*)
                |
                (?:(?:x|times?)\s*)
            )
            {unit_pattern}
            \b
        """)

        if unit_name == "hour":
            
            replacement = (
                n * n_per_day[unit_name]
            )

        elif unit_name == "day":

            replacement = n

        else:

            replacement = (
                n / n_per_day[unit_name]
            )


        rows.append({
            "raw": pattern_standard,
            "replacement": replacement,
            "priority": 1,
            "notes": f"{n} per {unit_name}"
        })


        # =================================================
        # Pattern 2
        # ex:
        # 2 weekly
        # 3 monthly
            # =================================================

        if unit_name in adverb_units:
            
            adverb_pattern = (
                adverb_units[unit_name]["pattern"]
            )

            pattern_adverb = re.sub(r"\s+", "", rf"""
                \b
                (?:{n}(?:\.0+)?|{word})
                \s+
                {adverb_pattern}
                \b
            """)

        # -----------------------------------------
        # ADVERB REPLACEMENT
        # ex:
        # 2 weekly  = 2/7
        # 3 monthly = 3/30
        # 2 hourly  = 2*24
        # -----------------------------------------

        if unit_name == "hour":

            replacement_adverb = (
                n * 24
            )

        else:

            replacement_adverb = (
                n / adverb_units[unit_name]["days"]
            )

        rows.append({

            "raw": pattern_adverb,

            "replacement": replacement_adverb,

            "priority": 1,

            "notes": f"{n} {unit_name} adverb"
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
        if unit_name == 'hour' :
            replacement = n_per_day[unit_name]/n
        else : 
            replacement = 1 / (n * n_per_day[unit_name])

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
        every\s+(?:{n}(?:\.0+)?|{word})
        \s+
        {unit_pattern}
        \b
        """)

        # ✅ NEW LOGIC (interval-based)

        if unit_name == 'hour' :
            replacement = n_per_day[unit_name]/n
        else : 
            replacement = 1 / (n * n_per_day[unit_name])

        rows.append({
            "raw": pattern_every,
            "replacement": replacement,
            "priority": 1,
            "notes": f"every {n} {unit_name}"
        })



for n, word in num_words.items():
    time_units_no_day = {
    "week": r"(?:weekly|weeks|week|wks|wk|w)",
    "month": r"(?:monthly|months|month|mo|m)",
    "year": r"(?:annually|yearly|year|yr|y)",
    "hour": r"(?:hours|hour|hrs|hr|h)"
    }

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

        replacement = n / n_per_day[unit_name]


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

        replacement = n / n_per_day[unit_name]


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
    "priority": 2,
    "notes": "once (no unit)"
})

# stand alone twice
rows.append({
    "raw": r"\btwice\b",
    "replacement": "2x",
    "priority": 2,
    "notes": "twice (no unit)"
})



df = pd.DataFrame(rows)
df['category'] = "frequency"
df_norm = pd.read_csv("/Users/emudr/PPMI_LEDD/data/frequency_dictionary_manual.csv")
df_combined = pd.concat([df_norm, df], ignore_index=True)
df_combined = df_combined.drop_duplicates(subset=["raw", "replacement"])
df_combined = df_combined.sort_values(by=["priority", "replacement"])
df_combined.to_csv("/Users/emudr/PPMI_LEDD/data/frequency_dictionary.csv", index=False)