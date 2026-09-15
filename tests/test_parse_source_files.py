"""Unit tests for date-parsing logic in parse_source_files.py."""
from datetime import date, datetime

from parse_source_files import _parse_usa_int_date, _parse_generic_date


# --- _parse_usa_int_date (USA's ambiguous integer date format) ---

def test_usa_date_7_digit_single_digit_month():
    # 6152022 -> 6/15/2022
    result, note = _parse_usa_int_date(6152022)
    assert result == date(2022, 6, 15)
    assert note is None


def test_usa_date_8_digit_double_digit_month():
    # 12282021 -> 12/28/2021
    result, note = _parse_usa_int_date(12282021)
    assert result == date(2021, 12, 28)
    assert note is None


def test_usa_date_missing_value():
    result, note = _parse_usa_int_date(None)
    assert result is None
    assert note == "missing date"


def test_usa_date_unparseable_length():
    # A 5-digit value doesn't match either expected format.
    result, note = _parse_usa_int_date(12345)
    assert result is None
    assert "unparseable" in note


# --- _parse_generic_date (used for IND / AUS sources) ---

def test_generic_date_from_datetime_object():
    dt = datetime(1998, 12, 1)
    result, note = _parse_generic_date(dt)
    assert result == date(1998, 12, 1)
    assert note is None


def test_generic_date_literal_null_string():
    # AUS.xlsx contains the literal string 'NULL' instead of a blank.
    result, note = _parse_generic_date("NULL")
    assert result is None
    assert "literal 'NULL'" in note


def test_generic_date_invalid_calendar_date():
    # AUS.xlsx contains '2021-13-13' -- month 13 doesn't exist.
    result, note = _parse_generic_date("2021-13-13")
    assert result is None
    assert "invalid date value" in note


def test_generic_date_valid_string():
    result, note = _parse_generic_date("2022-03-12")
    assert result == date(2022, 3, 12)
    assert note is None


def test_generic_date_missing_value():
    result, note = _parse_generic_date(None)
    assert result is None
    assert note == "missing date"