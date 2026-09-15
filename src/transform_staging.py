"""
Takes the standardized staging DataFrame from parse_source_files.py and:
  1. Derives AGE (from DOB) and STALE_MEMBER (days since FLIGHT_DATE > 90)
  2. Splits members into per-country DataFrames, applying "latest record
     wins" when the same MEMBER_ID appears more than once (a member who
     has moved countries or been re-issued a record) based on the most
     recent ENROLLMENT_DATE.
"""

from __future__ import annotations
import logging
from datetime import date

import pandas as pd

from parse_source_files import load_all_sources
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

STALE_THRESHOLD_DAYS = 90


def compute_age(dob: date | None, as_of: date | None = None) -> int | None:
    """Age in whole years as of `as_of` (defaults to today). None if DOB missing."""
    if dob is None:
        return None
    as_of = as_of or date.today()
    years = as_of.year - dob.year
    had_birthday_yet = (as_of.month, as_of.day) >= (dob.month, dob.day)
    return years if had_birthday_yet else years - 1


def compute_stale_member(flight_date: date | None, as_of: date | None = None) -> bool | None:
    """True if days since last flight > 90. None if FLIGHT_DATE missing (unknown, not False)."""
    if flight_date is None:
        return None
    as_of = as_of or date.today()
    return (as_of - flight_date).days > STALE_THRESHOLD_DAYS


def add_derived_columns(staging_df: pd.DataFrame) -> pd.DataFrame:
    df = staging_df.copy()
    df["AGE"] = df["DOB"].apply(compute_age)
    df["STALE_MEMBER"] = df["FLIGHT_DATE"].apply(compute_stale_member)
    return df


def split_by_country_latest_wins(staging_df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """
    Groups by COUNTRY. Within each country, if a MEMBER_ID appears more
    than once, keeps only the row with the latest ENROLLMENT_DATE
    ("latest record wins"). Rows with a NULL ENROLLMENT_DATE are treated
    as oldest (sorted last) so a bad/missing date never wins over a valid one.
    """
    df = staging_df.copy()
    df["_sort_key"] = df["ENROLLMENT_DATE"].fillna(date.min)

    result: dict[str, pd.DataFrame] = {}
    for country, group in df.groupby("COUNTRY"):
        before = len(group)
        deduped = (
            group.sort_values("_sort_key", ascending=False)
                 .drop_duplicates(subset="MEMBER_ID", keep="first")
                 .drop(columns="_sort_key")
        )
        dropped = before - len(deduped)
        if dropped:
            logger.info("%s: dropped %d superseded record(s) via latest-record-wins", country, dropped)
        result[country] = deduped
    return result


if __name__ == "__main__":
    base_dir = Path(__file__).resolve().parent.parent / "sample_data"
    staging_df = add_derived_columns(load_all_sources(base_dir))
    print("--- Staging with Age / Stale_Member ---")
    print(staging_df[["MEMBER_ID", "MEMBER_NAME", "COUNTRY", "AGE", "STALE_MEMBER", "DATA_QUALITY_NOTES"]].to_string())

    country_tables = split_by_country_latest_wins(staging_df)
    for country, table in country_tables.items():
        print(f"\n--- {country} ({len(table)} members) ---")
        print(table[["MEMBER_ID", "MEMBER_NAME", "AGE", "STALE_MEMBER"]].to_string())