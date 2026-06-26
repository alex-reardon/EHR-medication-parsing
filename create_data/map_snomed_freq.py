import re
import pandas as pd

# -------------------------------
# unit → per day conversion
# -------------------------------
UNIT_TO_DAY = {
    "day": 1,
    "daily" : 1, 
    "week": 1/7,
    "weekly" : 1/7, 
    "month": 1/30,
    "monthly" : 1/30, 
    "yearly" : 1/365,
    "year": 1/365,
    "hour": 1/24,
    "hours" : 1/24, 
    "hourly" : 1/24,
    "minute": 1440, 
    "minutes" : 1440
}



# -------------------------------
# main function
# -------------------------------
def extract_frequency_per_day(text):
    if pd.isna(text):
        return None

    text = str(text).lower()

    # -------------------------------
    # remove qualifier noise
    # -------------------------------
    text = re.sub(r"\([^)]*qualifier[^)]*\)", "", text)

    # -------------------------------
    # PRN / unknown
    # -------------------------------
    if re.search(r"\b(prn|as needed|as required|when required)\b", text):
        return None

    # -------------------------------
    # 1. HANDLE "X-Y x / unit"
    # -------------------------------
    match = re.search(r"(\d+)\s*[-to]+\s*(\d+)\s*x\s*/\s*(day|daily|week|month|year|hour|hours|hourly)", text)
    if match:
        low, high, unit = match.groups()
        avg = (int(low) + int(high)) / 2
        return avg * UNIT_TO_DAY[unit]

    # -------------------------------
    # 2. HANDLE "X x / unit"
    # -------------------------------
    match = re.search(r"(\d+)\s*x\s*/\s*(day|daily|week|month|year|hour|hours|hourly)", text)
    if match:
        val, unit = match.groups()
        return int(val) * UNIT_TO_DAY[unit]

    # -------------------------------
    # 3. HANDLE "X times per unit"
    # -------------------------------
    match = re.search(r"(\d+)\s*(?:x|times?)\s*(?:per|a)?\s*(day|daily|week|month|year|hour|hours|hourly)", text)
    if match:
        val, unit = match.groups()
        return int(val) * UNIT_TO_DAY[unit]

    # -------------------------------
    # 4. HANDLE "every N hours/minutes/days"
    # -------------------------------
    match = re.search(r"every\s+(\d+)\s*(minute|minutes|day|days|daily|week|weeks|month|year|hour|hours|hourly)s?", text)
    if match:
        val, unit = match.groups()
        val = int(val)

        if unit == "hour" or unit == "hours" or unit == "hourly":
            return 24 / val
        elif unit == "minute":
            return 1440 / val
        elif unit == "day" or unit == "days":
            return 1 / val
        elif unit == "week" or unit == "weeks":
            return (1 / val) * (1/7)
        elif unit == "month":
            return (1 / val) * (1/30)
        elif unit == "year":
            return (1 / val) * (1/365)


    match = re.search(r"every\s+(\d+)\s*[-to]+\s*(\d+)\s*(minute|minutes|day|days|daily|week|weeks|month|year|hour|hours|hourly)s?", text)
    if match:
        low, high, unit = match.groups()
        val = (int(low) + int(high)) / 2

        if unit == "hour" or unit == "hours" or unit == "hourly":
            return 24 / val
        elif unit == "minute":
            return 1440 / val
        elif unit == "day" or unit == "days":
            return 1 / val
        elif unit == "week" or unit == "weeks":
            return (1 / val) * (1/7)
        elif unit == "month":
            return (1 / val) * (1/30)
        elif unit == "year":
            return (1 / val) * (1/365)

    match = re.search(
    r"(\d+)\s*(?:x|times?)?\s*(?:/|per|a)?\s*(day|daily|week|month|year|hour|hours|hourly)",
    text
    )

    if match:
        val, unit = match.groups()
        return int(val) * UNIT_TO_DAY[unit]

    # -------------------------------
    # 5. HANDLE shorthand qXh
    # -------------------------------
    match = re.search(r"\bq(\d+)\s*(h|hr|min|day|daily|wk|mo)\b", text)
    if match:
        val, unit = match.groups()
        val = int(val)

        if unit in ["h", "hr"]:
            return 24 / val
        elif unit == "min":
            return 1440 / val
        elif unit == "day":
            return 1 / val
        elif unit == "wk":
            return (1 / val) * (1/7)
        elif unit == "mo":
            return (1 / val) * (1/30)

    # -------------------------------
    # 6. SIMPLE known cases
    # -------------------------------
    if "once daily" in text or "once a day" in text or text.strip() == "daily":
        return 1

    if "twice daily" in text or "twice a day" in text:
        return 2

    if "three times daily" in text:
        return 3

    if "four times daily" in text:
        return 4

    # -------------------------------
    # fallback
    # -------------------------------
    return None


df = pd.read_csv('/Users/emudr/PPMI_LEDD/data/snomed_all_frequency_terms.csv')
df = df[~df["raw"].str.contains("qualifier value", case=False, na=False)]



import re

UNIT_NORMALIZATION = [
    # ---------------- DAY ----------------
    (r"\b(daily|each\s*day|per\s*day|a\s*day|q\s*day|every\s*day|days?)\b", "day"),

    # ---------------- WEEK ----------------
    (r"\b(weekly|per\s*week|a\s*week|each\s*week|every\s*week|weeks?|wk|wks)\b", "week"),

    # ---------------- MONTH ----------------
    (r"\b(monthly|per\s*month|a\s*month|each\s*month|every\s*month|months?|mo|mos|mth|mths)\b", "month"),

    # ---------------- YEAR ----------------
    (r"\b(yearly|annually|per\s*year|a\s*year|each\s*year|every\s*year|years?|yr|yrs|annually)\b", "year"),

    # ---------------- HOUR ----------------
    (r"\b(hourly|per\s*hour|a\s*hour|each\s*hour|every\s*hour|hours?|hr|hrs|h)\b", "hour"),

    # ---------------- MINUTE ----------------
    (r"\b(per\s*minute|a\s*minute|each\s*minute|every\s*minute|minutes?|min|mins)\b", "minute"),
]


def normalize_units(text):
    if text is None:
        return text

    text = str(text).lower()

    for pattern, replacement in UNIT_NORMALIZATION:
        text = re.sub(pattern, replacement, text)

    return text

df["map"] = df["canonical"].apply(normalize_units)

import re

num_map = {
    "zero": "0","one": "1","two": "2","three": "3","four": "4",
    "five": "5","six": "6","seven": "7","eight": "8","nine": "9",
    "ten": "10","eleven": "11","twelve": "12","thirteen": "13",
    "fourteen": "14","fifteen": "15","sixteen": "16",
    "seventeen": "17","eighteen": "18","nineteen": "19",
    "twenty": "20", "once" : "1", "twice" : "2", "every other" : "every 2"
}

pattern = re.compile(
    r"\b(" + "|".join(sorted(num_map.keys(), key=len, reverse=True)) + r")\b"
)

def replace_numbers(text):
    if pd.isna(text):
        return text
    return pattern.sub(lambda m: num_map[m.group(0)], str(text).lower())

df["map"] = df["map"].apply(replace_numbers)


df["replacement"] = df["map"].apply(extract_frequency_per_day)

df["raw"] = df["raw"].astype(str).apply(
    lambda x: x if x.startswith(r"\b") and x.endswith(r"\b") else rf"\b{x.strip()}\b"
)

df = df[df["replacement"].notna()]
df['category'] = 'frequency' 
df.rename(columns={'canonical':'notes'}, inplace = True)
df['priority'] =1
df = df[['raw', 'replacement', 'priority', 'category', 'notes']]
df.to_csv('/Users/emudr/PPMI_LEDD/data/snomed_mapped.csv')