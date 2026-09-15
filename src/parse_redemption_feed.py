"""
Parses the semi-structured JSON redemption feed into a flat, queryable
table (one row per redemption transaction), ready to load into a
Snowflake table like STAGING_REDEMPTIONS.

Join back to member data: each transaction row keeps MEMBER_ID, which is
the same key used in STAGING_MEMBERS / the country target tables — so
redemptions join to member profiles on MEMBER_ID (see note at bottom).
"""

from __future__ import annotations
import json
import logging
from pathlib import Path

import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

FLAT_COLUMNS = [
    "MEMBER_ID", "FEED_DATE", "TXN_ID", "TXN_DATE",
    "PARTNER", "MILES_REDEEMED", "STATUS", "SOURCE_FILE_NAME",
]


def flatten_redemption_feed(payload: dict, source_file_name: str) -> pd.DataFrame:
    """Flattens one feed document's nested `redemptions` array into rows."""
    member_id = payload.get("member_id")
    feed_date = payload.get("feed_date")
    redemptions = payload.get("redemptions", [])

    rows = []
    for txn in redemptions:
        rows.append({
            "MEMBER_ID": member_id,
            "FEED_DATE": feed_date,
            "TXN_ID": txn.get("txn_id"),
            "TXN_DATE": txn.get("txn_date"),
            "PARTNER": txn.get("partner"),
            "MILES_REDEEMED": txn.get("miles_redeemed"),
            "STATUS": txn.get("status"),
            "SOURCE_FILE_NAME": source_file_name,
        })
    return pd.DataFrame(rows, columns=FLAT_COLUMNS)


def parse_feed_file(path: Path) -> pd.DataFrame:
    with open(path, "r", encoding="utf-8") as f:
        payload = json.load(f)
    df = flatten_redemption_feed(payload, path.name)
    logger.info("Flattened %d transaction(s) from %s", len(df), path.name)
    return df


if __name__ == "__main__":
    base_dir = Path(__file__).resolve().parent.parent / "sample_data"
    redemptions_df = parse_feed_file(base_dir / "sample_redemptions.json")
    print(redemptions_df.to_string())

    # --- Join-back demonstration ---
    # In Snowflake this is simply:
    #   SELECT r.*, m.MEMBER_NAME, m.TIER_CODE, m.COUNTRY
    #   FROM STAGING_REDEMPTIONS r
    #   JOIN STAGING_MEMBERS m ON r.MEMBER_ID = m.MEMBER_ID
    # Here, joining against the staging output from transform_staging.py:
    from transform_staging import add_derived_columns
    from parse_source_files import load_all_sources

    members_df = add_derived_columns(load_all_sources(base_dir))
    joined = redemptions_df.merge(
        members_df[["MEMBER_ID", "MEMBER_NAME", "TIER_CODE", "COUNTRY"]],
        on="MEMBER_ID", how="left",
    )
    print("\n--- Joined redemptions + member profile ---")
    print(joined.to_string())