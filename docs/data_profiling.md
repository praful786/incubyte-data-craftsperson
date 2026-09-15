# Data Profiling Notes — SkyPoints Source Files

## Note on discrepancy from the assessment PDF
The PDF's sample flat file (pipe-delimited, with Member_Id, State, Country,
Agent_Name, Is_Active) does not match the actual files provided
(IND.xlsx, USA.xlsx, AUS.xlsx). Each country file has its own distinct
schema, is missing several PDF fields, and has its own data-quality issues.
This is treated as intentional — the pipeline is designed to be resilient
to real-world schema and quality variance, not just to the PDF's clean
sample.

## IND.xlsx
Columns: `ID, Name, DOB, TierCode, EnrollmentDate, Individual or Corporate, Flight Date`
- Dates are proper datetimes — clean.
- Extra field not in the PDF spec: `Individual or Corporate` (I/C flag).
- Missing PDF fields: Agent_Name, State, Country, Post Code, Is_Active.
  Country is only known from the filename.

Sample:
| ID | Name | DOB | TierCode | EnrollmentDate | Individual or Corporate | Flight Date |
|----|------|-----|----------|-----------------|---------------------------|--------------|
| 1 | Vikas | 1998-12-01 | SLV | 2022-01-01 | I | 2022-06-15 |
| 2 | Rahul | 1982-08-13 | GLD | 2022-03-05 | C | 2022-03-10 |

## USA.xlsx
Columns: `ID, Name, TierCode, EnrollmentDate, FlightDate`
- **No DOB column** — Age cannot be derived for USA members from this file.
- Dates are raw integers with no separators or fixed width, e.g.
  `6152022` = 6/15/2022, `1052022` = 1/5/2022, `12282021` = 12/28/2021.
  This is genuinely ambiguous and needs explicit parsing logic, not a
  simple date cast.

Sample:
| ID | Name | TierCode | EnrollmentDate | FlightDate |
|----|------|----------|------------------|-------------|
| 1 | Sam | PLT | 6152022 | 8202022 |
| 2 | John | SLV | 1052022 | 1152022 |

## AUS.xlsx
Columns: `Unique ID, Member Name, Tier Type, Date of Birth, Date of Enrollment, Date of Flight`
- Contains the **literal string `'NULL'`** in Date of Birth (not a true
  blank) — must be explicitly handled or it silently breaks downstream casts.
- Contains an **invalid date `'2021-13-13'`** in Date of Enrollment
  (month 13 doesn't exist) — must be caught by validation, not silently parsed.

Sample:
| Unique ID | Member Name | Tier Type | Date of Birth | Date of Enrollment | Date of Flight |
|-----------|--------------|-----------|-----------------|----------------------|-----------------|
| 1 | Mike | PLT | NULL | 2022-05-11 | 2022-08-01 |
| 2 | Jonnathan | GLD | 1997-12-13 | 2021-13-13 | 2022-01-05 |

## Design implications
1. Land data close to raw (mostly VARCHAR) so bad values (AUS's invalid
   date, the `'NULL'` string) never fail the load — casting and
   validation happen in staging, not landing.
2. Map each source's distinct columns into one canonical staging schema
   aligned to the PDF's layout (Member_Name, Member_Id, Enrollment_Date,
   Last_Flight_Date, Tier_Code, Agent_Name, State, Country, DOB,
   Is_Active), filling missing source fields with NULL, plus a
   `Data_Quality_Notes` column to record row-level issues instead of
   dropping rows silently.
3. USA needs custom date-parsing logic due to its ambiguous integer format.
4. Country isn't a column in any file — it's derived from the source
   filename/feed at ingestion time.
5. Age can't be computed for USA members (no DOB); staging must allow
   Age to be NULL with a documented reason rather than failing the row.