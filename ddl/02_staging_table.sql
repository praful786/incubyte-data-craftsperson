-- Unified staging table. All three raw sources land here in one
-- canonical schema aligned to the PDF's detail-record layout, with
-- derived Age/Stale_Member columns and a data-quality notes column
-- instead of silently dropping bad rows.

CREATE OR REPLACE TABLE STAGING_MEMBERS (
    MEMBER_ID               VARCHAR,
    MEMBER_NAME              VARCHAR,
    DOB                      DATE,
    AGE                      NUMBER,          -- derived; NULL if DOB missing/invalid
    TIER_CODE                VARCHAR,
    ENROLLMENT_DATE          DATE,
    FLIGHT_DATE              DATE,
    STALE_MEMBER             BOOLEAN,         -- TRUE if days since FLIGHT_DATE > 90
    AGENT_NAME               VARCHAR,         -- not present in any source file; NULL
    STATE                    VARCHAR,         -- not present in any source file; NULL
    COUNTRY                  VARCHAR,         -- derived from source file, not a column
    IS_ACTIVE                VARCHAR,         -- not present in any source file; NULL
    INDIVIDUAL_OR_CORPORATE  VARCHAR,         -- only present in IND source; NULL for others
    DATA_QUALITY_NOTES       VARCHAR,         -- e.g. 'invalid enrollment date', 'missing DOB'
    SOURCE_FILE_NAME         VARCHAR,
    LOAD_TS                  TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);