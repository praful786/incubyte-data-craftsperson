"""Unit tests for the validation checks in validate_data.py."""
import pandas as pd

from validate_data import check_mandatory_fields, check_key_uniqueness, check_data_quality_notes


def _row(member_id, country, member_name="X", enrollment_date="2022-01-01", notes=None):
    return {
        "MEMBER_ID": member_id, "MEMBER_NAME": member_name, "DOB": None,
        "TIER_CODE": "GLD", "ENROLLMENT_DATE": enrollment_date,
        "FLIGHT_DATE": None, "AGENT_NAME": None, "STATE": None,
        "COUNTRY": country, "IS_ACTIVE": None,
        "INDIVIDUAL_OR_CORPORATE": None, "DATA_QUALITY_NOTES": notes,
        "SOURCE_FILE_NAME": "test.xlsx",
    }


# --- check_mandatory_fields ---

def test_mandatory_fields_flags_missing_name():
    df = pd.DataFrame([_row("1", "INDIA", member_name=None)])
    issues = check_mandatory_fields(df)
    assert len(issues) == 1
    assert "MEMBER_NAME is missing" in issues.iloc[0]["DETAIL"]


def test_mandatory_fields_flags_missing_enrollment_date():
    df = pd.DataFrame([_row("1", "AUSTRALIA", enrollment_date=None)])
    issues = check_mandatory_fields(df)
    assert len(issues) == 1
    assert "ENROLLMENT_DATE is missing" in issues.iloc[0]["DETAIL"]


def test_mandatory_fields_no_issues_when_all_present():
    df = pd.DataFrame([_row("1", "USA")])
    issues = check_mandatory_fields(df)
    assert len(issues) == 0


# --- check_key_uniqueness ---

def test_key_uniqueness_flags_duplicate_member_id_within_country():
    # check_key_uniqueness reports once per distinct duplicated MEMBER_ID,
    # not once per row -- two rows sharing MEMBER_ID "1" yields one issue.
    df = pd.DataFrame([_row("1", "INDIA"), _row("1", "INDIA")])
    issues = check_key_uniqueness(df)
    assert len(issues) == 1
    assert issues.iloc[0]["CHECK"] == "duplicate_key"


def test_key_uniqueness_same_id_different_country_not_flagged():
    df = pd.DataFrame([_row("1", "INDIA"), _row("1", "USA")])
    issues = check_key_uniqueness(df)
    assert len(issues) == 0


# --- check_data_quality_notes ---

def test_data_quality_notes_surfaced_as_issues():
    df = pd.DataFrame([
        _row("1", "AUSTRALIA", notes="invalid date value: '2021-13-13'"),
        _row("2", "USA", notes=None),
    ])
    issues = check_data_quality_notes(df)
    assert len(issues) == 1
    assert issues.iloc[0]["MEMBER_ID"] == "1"