import requests
import pandas as pd
import time

# -----------------------------
# CONFIG
# -----------------------------
EXPAND_URL = "https://r4.ontoserver.csiro.au/fhir/ValueSet/$expand"
LOOKUP_URL = "https://r4.ontoserver.csiro.au/fhir/CodeSystem/$lookup"

HEADERS = {"Accept": "application/json"}

ROOT_CODES = [
    "307438009",
    "307454007",
    "307444008",
    "307432005",
    "307431003",
    "307459002",
    "307449003",
    "307467005", 
    "229799001", 
    "307439001", 
    "229798009"
]

COUNT = 1000


# -----------------------------
# STEP 1: GET CONCEPTS FOR ONE ROOT
# -----------------------------
def get_concepts_for_root(root_code):
    all_concepts = []
    offset = 0

    while True:
        params = {
            "url": f"http://snomed.info/sct?fhir_vs=ecl/<<{root_code}",
            "count": COUNT,
            "offset": offset
        }

        r = requests.get(EXPAND_URL, params=params, headers=HEADERS)
        data = r.json()

        batch = data.get("expansion", {}).get("contains", [])
        if not batch:
            break

        all_concepts.extend(batch)
        offset += len(batch)

    return all_concepts


# -----------------------------
# STEP 2: GET SYNONYMS
# -----------------------------
def get_synonyms(code):
    params = {
        "system": "http://snomed.info/sct",
        "code": code
    }

    r = requests.get(LOOKUP_URL, params=params, headers=HEADERS)
    data = r.json()

    syns = []
    for p in data.get("parameter", []):
        if p["name"] == "designation":
            for part in p.get("part", []):
                if part["name"] == "value":
                    syns.append(part["valueString"])

    return syns


# -----------------------------
# STEP 3: BUILD DATASET
# -----------------------------
rows = []
seen_codes = set()

for root in ROOT_CODES:
    print(f"Processing root: {root}")

    concepts = get_concepts_for_root(root)

    for concept in concepts:
        code = concept["code"]
        display = concept["display"]

        # avoid duplicate lookups across roots
        if code in seen_codes:
            continue
        seen_codes.add(code)

        synonyms = get_synonyms(code)

        for s in synonyms:
            rows.append({
                "raw": s.lower(),
                "canonical": display.lower(),
                "snomed_code": code,
                "root_category": root
            })

        time.sleep(0.1)  # avoid rate limiting


# -----------------------------
# STEP 4: SAVE CSV
# -----------------------------
df = pd.DataFrame(rows)

df = df.drop_duplicates()

df.to_csv("/Users/emudr/Desktop/snomed_all_frequency_terms.csv", index=False)

print(f"Saved {len(df)} rows to snomed_all_frequency_terms.csv")
