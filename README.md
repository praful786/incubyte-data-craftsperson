# SkyPoints Membership Data Pipeline — Incubyte Data Craftsperson Assessment

## Problem
SkyPoints is a global airline loyalty program. Member data currently
lives in one database and needs to be split per-country for scale
(millions of members, billions of records/day expected). Two daily
feeds arrive: a flat file of member profiles, and a JSON feed of
partner-airline mileage redemptions. This repo implements the
raw → staging → country-split pipeline, plus JSON parsing and
validations, as specified in the assessment PDF.

## A note on the actual source data
The three files provided (`IND.xlsx`, `USA.xlsx`, `AUS.xlsx`) don't
match the PDF's sample flat-file layout — each has its own schema and
its own data-quality issues (USA has no DOB column and stores dates as
ambiguous integers; Australia has a literal `'NULL'` string and an
invalid date `'2021-13-13'`). Rather than normalize this away, the
pipeline is deliberately built to be resilient to it — see
[`docs/data_profiling.md`](docs/data_profiling.md) for the full
breakdown, since this shaped most of the design decisions below.

## Architecture

Raw source files (xlsx / JSON)
|
v
RAW_MEMBER_IND / RAW_MEMBER_USA / RAW_MEMBER_AUS (land as-is, VARCHAR)
RAW_REDEMPTION_JSON (land as VARIANT)
|
v
STAGING_MEMBERS (unified schema, Age/Stale_Member derived,
bad values flagged in DATA_QUALITY_NOTES
instead of dropped)
STAGING_REDEMPTIONS (flattened from JSON)
|
v
TABLE_INDIA / TABLE_USA / TABLE_AUSTRALIA
("latest record wins" applied per MEMBER_ID)


Design principle throughout: **land everything, fail nothing, flag
problems explicitly.** A malformed row never breaks the load — it
shows up in `DATA_QUALITY_NOTES` and in the validation report instead.

## Repo structure
- `ddl/` — Snowflake DDL for raw, staging, country target, and
  redemption tables, plus SQL validation checks
- `src/` — Python implementation of parsing, transformation, and
  validation logic
- `sample_data/` — the three source files + a sample JSON feed
- `docs/` — data profiling notes
- `tests/` — unit tests (see below)

## How to run
```bash
cd src
pip install pandas openpyxl

python parse_source_files.py       # parses all 3 country files into one staging DataFrame
python transform_staging.py        # adds Age/Stale_Member, splits by country with latest-record-wins
python parse_redemption_feed.py    # flattens the JSON feed and joins it back to member data
python validate_data.py            # runs mandatory-field, uniqueness, and data-quality checks
```

Each script is independently runnable and prints its output to the
console for inspection — this mirrors how the logic would run as
separate Snowflake load/transform steps in production.

## Key design decisions
- **Country split & "latest record wins":** implemented by sorting each
  country's records by `ENROLLMENT_DATE` descending and de-duplicating
  on `MEMBER_ID`, keeping the most recent. Rows with an unparseable
  enrollment date are sorted last so a bad date can never win over a
  valid one.
- **USA date parsing:** the raw integers (e.g. `6152022`) have no fixed
  width or separator, so they're parsed by string length rather than a
  simple cast — documented in `parse_source_files.py`.
- **JSON flattening:** each entry in the `redemptions` array becomes one
  row, carrying the parent `member_id`/`feed_date`. It joins to member
  profiles on `MEMBER_ID` — see `ddl/04_redemption_staging_table.sql`
  for the Snowflake `LATERAL FLATTEN` equivalent.
- **Validations:** mandatory-field checks, key-column uniqueness, and
  every row already flagged during parsing (bad dates, missing DOB,
  literal `'NULL'` strings) are all surfaced as first-class validation
  issues, not silently dropped.

## Use of AI tools
[Add 2-3 sentences here on how you used AI — be specific: e.g. "Used
Claude to design the raw/staging/target schema split, draft the Python
parsing logic for ambiguous date formats, and structure the validation
checks. I reviewed and adjusted [specific things] based on my own
understanding of the data." Be honest and specific — this is explicitly
evaluated.]

## Deliverables checklist
- [x] DDL — raw/landing, staging, country target tables
- [x] Staging load with Age and Stale_Member derived columns
- [x] Country-split transformation with latest-record-wins
- [x] JSON redemption feed parsing + join-back logic
- [x] Data validations (mandatory fields, key uniqueness, quality checks)
- [ ] Live demo (on request)