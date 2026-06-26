import math
import pytest

from postprocessing.cleanup import _clean_extraction_artifacts


def test_removes_empty_parentheses():
    assert _clean_extraction_artifacts("levodopa ()") == "levodopa"

def test_removes_unknown():
    assert _clean_extraction_artifacts("unknown drug") == "drug"

def test_removes_unk():
    assert _clean_extraction_artifacts("unk") == ""

def test_removes_trailing_slash():
    assert _clean_extraction_artifacts("levodopa/") == "levodopa"

def test_removes_dangling_slash_paren():
    assert _clean_extraction_artifacts("levodopa /(") == "levodopa"

def test_normalizes_plus_separator():
    assert _clean_extraction_artifacts("carbidopa + levodopa") == "carbidopa levodopa"

def test_normalizes_colon_separator():
    assert _clean_extraction_artifacts("dose: 100") == "dose 100"

def test_removes_double_slash():
    result = _clean_extraction_artifacts("levodopa // carbidopa")
    assert "//" not in result

def test_collapses_whitespace():
    assert _clean_extraction_artifacts("levodopa  carbidopa") == "levodopa carbidopa"

def test_strips_leading_trailing_whitespace():
    assert _clean_extraction_artifacts("  levodopa  ") == "levodopa"

def test_removes_trailing_nonalpha():
    assert _clean_extraction_artifacts("levodopa,,") == "levodopa"

def test_nan_passthrough():
    result = _clean_extraction_artifacts(float("nan"))
    assert isinstance(result, float) and math.isnan(result)

def test_clean_string_unchanged():
    assert _clean_extraction_artifacts("levodopa carbidopa") == "levodopa carbidopa"
