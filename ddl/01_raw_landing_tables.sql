-- Raw/landing layer: one table per source file, columns kept as VARCHAR
-- so malformed source values (bad dates, literal 'NULL' strings) never
-- fail the load. All cleansing/casting happens in staging, not here.

CREATE OR REPLACE TABLE RAW_MEMBER_IND (
    ID                          VARCHAR,
    NAME                        VARCHAR,
    DOB                         VARCHAR,
    TIER_CODE                   VARCHAR,
    ENROLLMENT_DATE             VARCHAR,
    INDIVIDUAL_OR_CORPORATE     VARCHAR,
    FLIGHT_DATE                 VARCHAR,
    SOURCE_FILE_NAME            VARCHAR,
    SOURCE_ROW_NUMBER           NUMBER,
    LOAD_TS                     TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

CREATE OR REPLACE TABLE RAW_MEMBER_USA (
    ID                          VARCHAR,
    NAME                        VARCHAR,
    TIER_CODE                   VARCHAR,
    ENROLLMENT_DATE             VARCHAR,   -- raw ambiguous integer, e.g. '6152022'
    FLIGHT_DATE                 VARCHAR,
    SOURCE_FILE_NAME            VARCHAR,
    SOURCE_ROW_NUMBER           NUMBER,
    LOAD_TS                     TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

CREATE OR REPLACE TABLE RAW_MEMBER_AUS (
    UNIQUE_ID                   VARCHAR,
    MEMBER_NAME                 VARCHAR,
    TIER_TYPE                   VARCHAR,
    DATE_OF_BIRTH               VARCHAR,   -- may literally contain the string 'NULL'
    DATE_OF_ENROLLMENT          VARCHAR,   -- may contain invalid dates, e.g. '2021-13-13'
    DATE_OF_FLIGHT               VARCHAR,
    SOURCE_FILE_NAME            VARCHAR,
    SOURCE_ROW_NUMBER           NUMBER,
    LOAD_TS                     TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- Raw landing for the semi-structured JSON redemption feed.
-- Land the whole payload as VARIANT; flattening happens later in staging.
CREATE OR REPLACE TABLE RAW_REDEMPTION_JSON (
    RAW_PAYLOAD                 VARIANT,
    SOURCE_FILE_NAME            VARCHAR,
    LOAD_TS                     TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);