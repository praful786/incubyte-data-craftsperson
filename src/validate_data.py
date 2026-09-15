"""
Runs data validation checks against the staging DataFrame and produces a
validation report. Doesn't halt the pipeline on failures — it flags rows,
consistent with the "land everything, flag problems" approach used
throughout (see docs/data_profiling.md).
"""

from __future__ import annotations
import logging
from pathlib import Path

import pandas as pd

from parse_source_files import load_all_sources
from transform_staging import add_derived_columns

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# Per the PDF's detail-record layout, these are the mandatory fields.
MANDATORY_FIELDS = ["MEMBER_ID", "MEMBER_NAME", "ENROLLMENT_DATE"]


def check_mandatory_fields(df: pd.DataFrame) -> pd.DataFrame:
    """Flags rows missing any mandatory field."""
    issues = []
    for field in MANDATORY_FIELDS:
        missing = df[df[field].isna()]
        for _, row in missing.iterrows():
            issues.append({
                "CHECK": "mandatory_field_missing",
                "MEMBER_ID": row["MEMBER_ID"],
                "COUNTRY": row["COUNTRY"],
                "DETAIL": f"{field} is missing",
            })
    return pd.DataFrame(issues)


def check_key_uniqueness(df: pd.DataFrame) -> pd.DataFrame:
    """
    Flags duplicate MEMBER_ID within the same country's raw feed (before
    latest-record-wins has been applied). A duplicate here is expected to
    be resolved by the country-split step, but is still worth reporting
    so it's visible that a collision occurred rather than being silent.
    """
    issues = []
    for country, group in df.groupby("COUNTRY"):
        dupe_ids = group["MEMBER_ID"][group["MEMBER_ID"].duplicated(keep=False)].unique()
        for member_id in dupe_ids:
            issues.append({
                "CHECK": "duplicate_key",
                "MEMBER_ID": member_id,
                "COUNTRY": country,
                "DETAIL": f"MEMBER_ID appears more than once in {country} source data "
                          f"(resolved by latest-record-wins at country-split stage)",
            })
    return pd.DataFrame(issues)


def check_data_quality_notes(df: pd.DataFrame) -> pd.DataFrame:
    """
    Surfaces every row that parse_source_files.py already flagged with a
    DATA_QUALITY_NOTES value (invalid dates, the literal 'NULL' string,
    missing DOB, etc.) as a first-class validation issue.
    """
    flagged = df[df["DATA_QUALITY_NOTES"].notna()]
    return pd.DataFrame([{
        "CHECK": "source_data_quality",
        "MEMBER_ID": row["MEMBER_ID"],
        "COUNTRY": row["COUNTRY"],
        "DETAIL": row["DATA_QUALITY_NOTES"],
    } for _, row in flagged.iterrows()])


def run_all_validations(df: pd.DataFrame) -> pd.DataFrame:
    checks = [check_mandatory_fields(df), check_key_uniqueness(df), check_data_quality_notes(df)]
    report = pd.concat(checks, ignore_index=True)
    logger.info("Validation complete: %d issue(s) found across %d rows", len(report), len(df))
    return report


if __name__ == "__main__":
    base_dir = Path(__file__).resolve().parent.parent / "sample_data"
    staging_df = add_derived_columns(load_all_sources(base_dir))
    report = run_all_validations(staging_df)
    print(report.to_string() if not report.empty else "No validation issues found.")