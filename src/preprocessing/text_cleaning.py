import pandas as pd
import re
import unicodedata




# -------------------------------
# BASIC TEXT NORMALIZATION
# -------------------------------
def normalize_unicode(text: str) -> str:
    return unicodedata.normalize("NFKC", str(text))


def lowercase_text(text: str) -> str:
    return text.lower()


def normalize_symbols(text : str) -> str:
    text = re.sub(r'\\', '/', text) #capture double //
    text = text.replace('[', '(').replace(']', ')')
    text = re.sub(r'/+', '/', text) #capture double //
    text = re.sub(r'\s*/\s*', '/', text) # normalize ' / ' 
    text = re.sub(r'[–—−]', '-', text)
    return text


def remove_invalid_characters(text : str) -> str:
    text = re.sub(r'[^a-z0-9\s\./\-%\(\)\+:,]',' ', text)
    return text


def remove_non_decimal_periods(text: str) -> str:
    text = re.sub(r'(?<!\d)\.(?!\d)', '', text) # only keep decimals if between two numbers 
    return text


def clean_whitespace(text : str) -> str:
    text = re.sub(r'\s+', ' ', text)# collapse whitespace
    return text



def normalize_text(text: str) -> str:
    if pd.isna(text):
    
        return text

    text = str(text)

    # unicode
    text = normalize_unicode(text)

    # lowercase
    text = lowercase_text(text)

    # normalize symbols 
    text = normalize_symbols(text)

    # normalize invalid characters
    text = remove_invalid_characters(text)

    # remove
    text = remove_non_decimal_periods(text)

    # whitespace
    text = clean_whitespace(text)

    return text
