"""
Parses the three country source files (IND.xlsx, USA.xlsx, AUS.xlsx) into
a single standardized staging DataFrame, handling each source's distinct
schema and data-quality issues (ambiguous USA date integers, AUS's
literal 'NULL' string and invalid dates).

Design choice: bad/unparseable values are NOT dropped or silently
defaulted. They're kept as NULL in the relevant column and explained in
DATA_QUALITY_NOTES, so downstream consumers can decide how to handle them.
"""

from __future__ import annotations
import logging
from datetime import date, datetime
from pathlib import Path

import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

STAGING_COLUMNS = [
    "MEMBER_ID", "MEMBER_NAME", "DOB", "TIER_CODE", "ENROLLMENT_DATE",
    "FLIGHT_DATE", "AGENT_NAME", "STATE", "COUNTRY", "IS_ACTIVE",
    "INDIVIDUAL_OR_CORPORATE", "DATA_QUALITY_NOTES", "SOURCE_FILE_NAME",
]


def _add_note(existing: str | None, note: str) -> str:
    """Appends a data-quality note, keeping any prior notes on the row."""
    return note if not existing else f"{existing}; {note}"


def _parse_usa_int_date(raw_value) -> tuple[date | None, str | None]:
    """
    USA dates are stored as ambiguous integers with no separators or
    fixed width, e.g. 6152022 -> 6/15/2022, 12282021 -> 12/28/2021.
    Strategy: convert to string, and split into month/day/year based on
    string length (7 chars = M-D-YYYY, 8 chars = MM-DD-YYYY).
    """
    if raw_value is None or (isinstance(raw_value, float) and pd.isna(raw_value)):
        return None, "missing date"
    s = str(int(raw_value))
    try:
        if len(s) == 7:              # e.g. 6152022 -> 6 15 2022
            month, day, year = int(s[0]), int(s[1:3]), int(s[3:])
        elif len(s) == 8:             # e.g. 12282021 -> 12 28 2021
            month, day, year = int(s[0:2]), int(s[2:4]), int(s[4:])
        else:
            return None, f"unparseable date format: '{s}'"
        return date(year, month, day), None
    except ValueError:
        return None, f"invalid date value: '{s}'"


def _parse_generic_date(raw_value) -> tuple[date | None, str | None]:
    """Handles dates that may already be datetimes, or bad strings like
    AUS's 'NULL' or '2021-13-13'."""
    if raw_value is None:
        return None, "missing date"
    if isinstance(raw_value, (datetime, date)):
        return (raw_value.date() if isinstance(raw_value, datetime) else raw_value), None
    if isinstance(raw_value, str):
        if raw_value.strip().upper() == "NULL":
            return None, "date stored as literal 'NULL' string"
        try:
            return datetime.strptime(raw_value.strip(), "%Y-%m-%d").date(), None
        except ValueError:
            return None, f"invalid date value: '{raw_value}'"
    return None, f"unrecognized date type: {raw_value!r}"


def load_india(path: Path) -> pd.DataFrame:
    df = pd.read_excel(path)
    rows = []
    for _, r in df.iterrows():
        dob, dob_note = _parse_generic_date(r.get("DOB"))
        enr, enr_note = _parse_generic_date(r.get("EnrollmentDate"))
        fl, fl_note = _parse_generic_date(r.get("Flight Date"))
        notes = None
        for n in (dob_note, enr_note, fl_note):
            if n:
                notes = _add_note(notes, n)
        rows.append({
            "MEMBER_ID": str(r.get("ID")), "MEMBER_NAME": r.get("Name"),
            "DOB": dob, "TIER_CODE": r.get("TierCode"),
            "ENROLLMENT_DATE": enr, "FLIGHT_DATE": fl,
            "AGENT_NAME": None, "STATE": None, "COUNTRY": "INDIA",
            "IS_ACTIVE": None,
            "INDIVIDUAL_OR_CORPORATE": r.get("Individual or Corporate"),
            "DATA_QUALITY_NOTES": notes, "SOURCE_FILE_NAME": path.name,
        })
    return pd.DataFrame(rows, columns=STAGING_COLUMNS)


def load_usa(path: Path) -> pd.DataFrame:
    df = pd.read_excel(path)
    rows = []
    for _, r in df.iterrows():
        enr, enr_note = _parse_usa_int_date(r.get("EnrollmentDate"))
        fl, fl_note = _parse_usa_int_date(r.get("FlightDate"))
        notes = "no DOB available in source file"
        for n in (enr_note, fl_note):
            if n:
                notes = _add_note(notes, n)
        rows.append({
            "MEMBER_ID": str(r.get("ID")), "MEMBER_NAME": r.get("Name"),
            "DOB": None, "TIER_CODE": r.get("TierCode"),
            "ENROLLMENT_DATE": enr, "FLIGHT_DATE": fl,
            "AGENT_NAME": None, "STATE": None, "COUNTRY": "USA",
            "IS_ACTIVE": None, "INDIVIDUAL_OR_CORPORATE": None,
            "DATA_QUALITY_NOTES": notes, "SOURCE_FILE_NAME": path.name,
        })
    return pd.DataFrame(rows, columns=STAGING_COLUMNS)


def load_australia(path: Path) -> pd.DataFrame:
    df = pd.read_excel(path)
    rows = []
    for _, r in df.iterrows():
        dob, dob_note = _parse_generic_date(r.get("Date of Birth"))
        enr, enr_note = _parse_generic_date(r.get("Date of Enrollment"))
        fl, fl_note = _parse_generic_date(r.get("Date of Flight"))
        notes = None
        for n in (dob_note, enr_note, fl_note):
            if n:
                notes = _add_note(notes, n)
        rows.append({
            "MEMBER_ID": str(r.get("Unique ID")), "MEMBER_NAME": r.get("Member Name"),
            "DOB": dob, "TIER_CODE": r.get("Tier Type"),
            "ENROLLMENT_DATE": enr, "FLIGHT_DATE": fl,
            "AGENT_NAME": None, "STATE": None, "COUNTRY": "AUSTRALIA",
            "IS_ACTIVE": None, "INDIVIDUAL_OR_CORPORATE": None,
            "DATA_QUALITY_NOTES": notes, "SOURCE_FILE_NAME": path.name,
        })
    return pd.DataFrame(rows, columns=STAGING_COLUMNS)


def load_all_sources(sample_data_dir: Path) -> pd.DataFrame:
    frames = [
        load_india(sample_data_dir / "IND.xlsx"),
        load_usa(sample_data_dir / "USA.xlsx"),
        load_australia(sample_data_dir / "AUS.xlsx"),
    ]
    combined = pd.concat(frames, ignore_index=True)
    logger.info("Loaded %d rows across %d source files", len(combined), len(frames))
    return combined


if __name__ == "__main__":
    base_dir = Path(__file__).resolve().parent.parent / "sample_data"
    staging_df = load_all_sources(base_dir)
    print(staging_df.to_string())