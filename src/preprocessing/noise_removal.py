import re

def remove_trailing_noise(text):
    text = re.sub(r'(?<=[a-z])\d{2,}$', '', text)
    text = re.sub(r'[^\w\s/+.-]+', ' ', text)
    text = re.sub(r'\.{2,}', ' ', text)
    return text