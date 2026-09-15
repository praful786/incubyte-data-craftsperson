-- Country-specific target tables. Same shape as staging, minus the
-- load-tracking columns, since Country is now fixed per table and
-- "latest record wins" dedup has already happened upstream.

CREATE OR REPLACE TABLE TABLE_INDIA (
    MEMBER_ID               VARCHAR PRIMARY KEY,
    MEMBER_NAME              VARCHAR,
    DOB                      DATE,
    AGE                      NUMBER,
    TIER_CODE                VARCHAR,
    ENROLLMENT_DATE          DATE,
    FLIGHT_DATE              DATE,
    STALE_MEMBER             BOOLEAN,
    AGENT_NAME               VARCHAR,
    STATE                    VARCHAR,
    IS_ACTIVE                VARCHAR,
    INDIVIDUAL_OR_CORPORATE  VARCHAR,
    LAST_UPDATED_TS          TIMESTAMP_NTZ
);

CREATE OR REPLACE TABLE TABLE_USA LIKE TABLE_INDIA;
CREATE OR REPLACE TABLE TABLE_AUSTRALIA LIKE TABLE_INDIA;