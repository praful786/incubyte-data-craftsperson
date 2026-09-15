-- Flattened, queryable redemption table (one row per transaction),
-- produced from RAW_REDEMPTION_JSON's VARIANT payload.
CREATE OR REPLACE TABLE STAGING_REDEMPTIONS (
    MEMBER_ID          VARCHAR,   -- FK: joins to STAGING_MEMBERS.MEMBER_ID
    FEED_DATE          DATE,
    TXN_ID             VARCHAR,
    TXN_DATE           DATE,
    PARTNER            VARCHAR,
    MILES_REDEEMED     NUMBER,
    STATUS             VARCHAR,
    SOURCE_FILE_NAME   VARCHAR,
    LOAD_TS            TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- Snowflake equivalent of the flattening step (if doing it in SQL
-- instead of Python), using LATERAL FLATTEN on the raw VARIANT:
--
-- INSERT INTO STAGING_REDEMPTIONS
-- SELECT
--     raw.RAW_PAYLOAD:member_id::VARCHAR,
--     raw.RAW_PAYLOAD:feed_date::DATE,
--     txn.value:txn_id::VARCHAR,
--     txn.value:txn_date::DATE,
--     txn.value:partner::VARCHAR,
--     txn.value:miles_redeemed::NUMBER,
--     txn.value:status::VARCHAR,
--     raw.SOURCE_FILE_NAME,
--     CURRENT_TIMESTAMP()
-- FROM RAW_REDEMPTION_JSON raw,
--      LATERAL FLATTEN(input => raw.RAW_PAYLOAD:redemptions) txn;
--
-- Join back to members:
-- SELECT r.*, m.MEMBER_NAME, m.TIER_CODE, m.COUNTRY
-- FROM STAGING_REDEMPTIONS r
-- JOIN STAGING_MEMBERS m ON r.MEMBER_ID = m.MEMBER_ID;