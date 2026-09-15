"""Unit tests for Age/Stale_Member derivation and the country-split
'latest record wins' logic in transform_staging.py."""
from datetime import date

import pandas as pd

from transform_staging import compute_age, compute_stale_member, split_by_country_latest_wins


# --- compute_age ---

def test_compute_age_birthday_already_passed_this_year():
    dob = date(1998, 1, 1)
    as_of = date(2026, 6, 1)
    assert compute_age(dob, as_of) == 28


def test_compute_age_birthday_not_yet_reached_this_year():
    dob = date(1998, 12, 25)
    as_of = date(2026, 6, 1)
    assert compute_age(dob, as_of) == 27


def test_compute_age_missing_dob_returns_none():
    assert compute_age(None) is None


# --- compute_stale_member ---

def test_stale_member_true_when_over_90_days():
    flight_date = date(2026, 1, 1)
    as_of = date(2026, 6, 1)  # 151 days later
    assert compute_stale_member(flight_date, as_of) is True


def test_stale_member_false_when_within_90_days():
    flight_date = date(2026, 5, 20)
    as_of = date(2026, 6, 1)  # 12 days later
    assert compute_stale_member(flight_date, as_of) is False


def test_stale_member_none_when_flight_date_missing():
    # Unknown, not False -- we shouldn't claim a member is "not stale"
    # when we don't actually know their last flight date.
    assert compute_stale_member(None) is None


# --- split_by_country_latest_wins ---

def _row(member_id, country, enrollment_date, name="X"):
    return {
        "MEMBER_ID": member_id, "MEMBER_NAME": name, "DOB": None,
        "TIER_CODE": "GLD", "ENROLLMENT_DATE": enrollment_date,
        "FLIGHT_DATE": None, "AGENT_NAME": None, "STATE": None,
        "COUNTRY": country, "IS_ACTIVE": None,
        "INDIVIDUAL_OR_CORPORATE": None, "DATA_QUALITY_NOTES": None,
        "SOURCE_FILE_NAME": "test.xlsx",
    }


def test_latest_record_wins_keeps_most_recent_enrollment():
    df = pd.DataFrame([
        _row("1", "INDIA", date(2022, 1, 1), name="Old"),
        _row("1", "INDIA", date(2023, 6, 1), name="New"),
    ])
    result = split_by_country_latest_wins(df)
    india = result["INDIA"]
    assert len(india) == 1
    assert india.iloc[0]["MEMBER_NAME"] == "New"


def test_latest_record_wins_no_duplicates_keeps_all_rows():
    df = pd.DataFrame([
        _row("1", "USA", date(2022, 1, 1)),
        _row("2", "USA", date(2022, 2, 1)),
    ])
    result = split_by_country_latest_wins(df)
    assert len(result["USA"]) == 2


def test_latest_record_wins_null_enrollment_date_never_wins():
    # A row with a missing/unparseable enrollment date should never be
    # preferred over a row with a genuine, valid date.
    df = pd.DataFrame([
        _row("1", "AUSTRALIA", None, name="BadDate"),
        _row("1", "AUSTRALIA", date(2021, 1, 1), name="ValidDate"),
    ])
    result = split_by_country_latest_wins(df)
    aus = result["AUSTRALIA"]
    assert len(aus) == 1
    assert aus.iloc[0]["MEMBER_NAME"] == "ValidDate"


def test_latest_record_wins_splits_by_country_separately():
    df = pd.DataFrame([
        _row("1", "INDIA", date(2022, 1, 1)),
        _row("1", "USA", date(2022, 1, 1)),
    ])
    result = split_by_country_latest_wins(df)
    # Same MEMBER_ID in two different countries is NOT a duplicate --
    # each country table gets its own row.
    assert len(result["INDIA"]) == 1
    assert len(result["USA"]) == 1