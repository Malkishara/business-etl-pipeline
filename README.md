# Hotel Booking ETL Pipeline

## Architecture

```
  generate_data.py
        |
        v
  data/raw/hotel_bookings.csv  ------------------------------> S3  raw/<date>/
        |
        v
  +-------------------------- run_pipeline.py --------------------------+
  |                                                                     |
  |  EXTRACT        TRANSFORM       REMOVE DUPES + VALIDATE     LOAD    |
  |  extract.py --> transform.py --> validate.py ------------> load.py  |
  |  read CSV       trim, casing,    de-duplicate,             batch    |
  |                 numeric + date   check constraints,        insert   |
  |                 conversion       split good / bad          (upsert) |
  +---------------------------------------------------------------------+
        |                                  |                        |
        v                                  v                        v
  data/cleaned/hotel_bookings_cleaned.csv  logs/rejected_records.csv   PostgreSQL
        |                                  |                       hotel_bookings
        v                                  v
  S3  processed/<date>/              S3  rejected/<date>/
```
**Tech stack:** Python 3.10+, pandas, psycopg2, boto3, python-dotenv, Faker, PostgreSQL 14+, AWS S3 (free tier).

## Project structure

```
business-etl-pipeline/
+-- run_pipeline.py            # single entry point: python run_pipeline.py
+-- requirements.txt
+-- .env.example                # template for secrets (copy to .env)
+-- .gitignore
+-- src/
|   +-- __init__.py
|   +-- extract.py              # read raw CSV
|   +-- generate_data.py           # creates the dirty raw dataset (20,300 rows)
|   +-- transform.py            # standardise text, numbers, dates
|   +-- validate.py             # de-duplicate + constraint validation
|   +-- load.py                 # PostgreSQL loading
|   +-- s3_utils.py             # S3 uploads
+-- database/
|   +-- schema.sql               # table, primary key, constraints
|   +-- indexes.sql              # indexes
|   +-- analytical_queries.sql   # analytical queries + EXPLAIN ANALYZE test
+-- data/
|   +-- raw/hotel_bookings.csv                 # raw (dirty) dataset
|   +-- cleaned/hotel_bookings_cleaned.csv     # cleaned output (generated)
+-- logs/
|   +-- rejected_records.csv     # rejected rows + reasons (generated)

```

## The dataset

**Domain:** hotel bookings. **Size:** 20,000 unique bookings + 300 duplicates = **20,300 raw rows** (requirement: 10,000+).
**Columns (9):**

| Column | Type | Example |
|---|---|---|
| `booking_id` | integer | 10001 |
| `customer_name` | string | Jane Smith |
| `hotel_name` | string | Ocean View Hotel |
| `country` | string | Sri Lanka |
| `room_type` | string | Deluxe |
| `price` | numeric | 245.50 |
| `rating` | numeric | 4.2 |
| `booking_date` | date | 2025-06-14 |
| `status` | string | Confirmed |

## Setup

**Prerequisites:** Python 3.10+, PostgreSQL 14+ (with `psql`), Git, an AWS account (free tier).

```powershell
# 1. Clone
git clone <your-repo-url>
cd business-etl-pipeline

# 2. Dependencies
pip install -r requirements.txt

# 3. Configuration (secrets live in .env, which is git-ignored)
copy .env.example .env          
# then open .env and fill in your real database password and AWS keys

# 4. Create the database (once)
psql -U postgres -c "CREATE DATABASE hotel_etl;"
```

All credentials (database and AWS) are read from **environment variables** loaded from `.env` via `python-dotenv`. **No secrets are hardcoded** anywhere in the code -- see `src/load.py` and `src/s3_utils.py`.

## Running the pipeline

```powershell
python src/generate_data.py      # 1. (re)create the raw dirty dataset in data/raw/
python run_pipeline.py       # 2. run the full ETL
```

Then create the indexes and explore the data:

```powershell
psql -U postgres -d hotel_etl -f database/indexes.sql
psql -U postgres -d hotel_etl -c "SELECT * FROM hotel_bookings LIMIT 10;"
psql -U postgres -d hotel_etl -f database/analytical_queries.sql
```

Example pipeline summary (fill in your real numbers after a run):

```
Raw records       : ___
Duplicate records : ___
Rejected records  : ___
Loaded records    : ___
```

## ETL steps in detail

### Extract (`src/extract.py`)
Reads `data/raw/hotel_bookings.csv` into a pandas DataFrame and prints the row count. The raw file is uploaded **unchanged** to S3 (`raw/`) immediately after extraction, so the original source is always preserved.

### Transform (`src/transform.py`)
| Task | How |
|---|---|
| Trim whitespace | `.str.strip()` on all text columns |
| Standardise casing | `.str.title()` on country, room type and status (`sri lanka`, `SRI LANKA` -> `Sri Lanka`) |
| Numeric types | `pd.to_numeric(errors="coerce")` for `booking_id`, `price`, `rating`; unparseable values (`N/A`, `unknown`) become missing |
| Date standardisation | `parse_dates()` tries each known format in turn (`%Y-%m-%d`, `%Y/%m/%d`, `%d/%m/%Y`, `%d-%m-%Y`, `%d-%b-%Y`); a value matching none becomes missing. Formats were chosen so no two can be confused with each other. |

### Validate (`src/validate.py`)
1. **Remove duplicates** on `booking_id` (keep the first). Duplicates are logged with reason `Duplicate booking_id`.
2. **Validate every remaining row.** A row is rejected if any of these fail:
   * a required field is missing (`Missing <column>`)
   * `price` is not greater than 0
   * `rating` is not between 1 and 5
   * `room_type` or `status` is not in the allowed set
3. A row can fail several checks at once; **all reasons are joined** into one `rejection_reason` string.

### Rejected records log
Every rejected row (invalid + duplicate) is saved to `logs/rejected_records.csv` with its `rejection_reason`, and uploaded to S3 (`rejected/`). Nothing is silently dropped, so rejected data can be reviewed or reprocessed later.

### Load (`src/load.py`)
* Connects using environment variables only (`DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`) -- no hardcoded credentials.
* Creates the table if it does not exist.
* Inserts rows with `execute_values` (one batched statement instead of one insert per row).
* Uses `ON CONFLICT (booking_id) DO NOTHING`, so re-running the pipeline is safe.
* Everything is committed in a single transaction: a failure part-way through leaves the table unchanged.

## Database design

Table: **`hotel_bookings`** (see `database/schema.sql`).

```sql
CREATE TABLE IF NOT EXISTS hotel_bookings (
    booking_id    INTEGER PRIMARY KEY,
    customer_name VARCHAR(255)  NOT NULL,
    hotel_name    VARCHAR(255)  NOT NULL,
    country       VARCHAR(100)  NOT NULL,
    room_type     VARCHAR(50)   NOT NULL,
    price         NUMERIC(10,2) NOT NULL CHECK (price > 0),
    rating        NUMERIC(2,1)  NOT NULL CHECK (rating >= 1 AND rating <= 5),
    booking_date  DATE          NOT NULL,
    status        VARCHAR(50)   NOT NULL
                  CHECK (status IN ('Confirmed','Cancelled','Completed','Pending'))
);
```

| Decision | Reason |
|---|---|
| `booking_id` **PRIMARY KEY** | uniquely identifies a booking; automatically creates a unique index; enables `ON CONFLICT` for safe re-runs |
| `NUMERIC(10,2)` for price | exact decimal arithmetic (never `FLOAT` for money) |
| `DATE` for booking_date | enables date functions and range filters instead of comparing text |
| `CHECK` constraints | the database itself refuses invalid prices, ratings and statuses -- a second line of defence after the Python validation |
| `NOT NULL` | required fields must always be present |


## Analytical queries

All queries are in `database/analytical_queries.sql`.

| # | Query | Business question | Technique |
|---|---|---|---|
| 1 | Top 10 hotels by revenue | Which hotels earn the most? | `GROUP BY`, `SUM`, `ORDER BY ... LIMIT 10` |
| 2 | Monthly revenue growth | How is revenue changing month to month? | CTE + `LAG()` window function |
| 3 | Average rating by country | Which markets are happiest? | `GROUP BY`, `AVG` |
| 4 | Revenue by room type | Which room types perform best? | `GROUP BY`, `SUM`, `AVG` |
| 5 | Booking status distribution | What share of bookings are cancelled? | `COUNT(*) / SUM(COUNT(*)) OVER ()` |

Revenue queries (1, 2 and 4) only count bookings with status **Confirmed** or **Completed**, since cancelled and pending bookings are not earned revenue.


## Performance and optimization

### Indexes (`database/indexes.sql`)

| Index | Serves | Why |
|---|---|---|
| `PRIMARY KEY (booking_id)` | lookups, de-duplication, upserts | created automatically, unique B-tree |
| `idx_booking_date (booking_date)` | date-range filters, monthly growth | B-tree supports range scans |
| `idx_country (country)` | average rating by country | speeds up filtering and grouping |
| `idx_status (status)` | status filters and distribution | frequent `WHERE status IN (...)` |
| `idx_hotel_name (hotel_name)` | hotel-based queries | grouping and filtering by hotel |
| `idx_status_booking_date (status, booking_date)` | queries filtering by status **and** date | composite index; the equality column (`status`) comes first, the range column (`booking_date`) second -- the correct order for a composite B-tree |

`ANALYZE hotel_bookings;` runs after index creation so the query planner has fresh statistics.

### Demonstrating the improvement

The performance test is at the bottom of `database/analytical_queries.sql`. Run it before and after the index exists and compare the plan and the **Execution Time**:

```sql
-- BEFORE: drop the date indexes
DROP INDEX IF EXISTS idx_booking_date;
DROP INDEX IF EXISTS idx_status_booking_date;

EXPLAIN ANALYZE
SELECT booking_id, hotel_name, price, booking_date
FROM hotel_bookings
WHERE booking_date >= '2026-01-01' AND booking_date < '2026-04-01';

-- AFTER: recreate the index (or just re-run database/indexes.sql)
CREATE INDEX idx_booking_date ON hotel_bookings (booking_date);
CREATE INDEX idx_status_booking_date ON hotel_bookings (status, booking_date);
ANALYZE hotel_bookings;

EXPLAIN ANALYZE
SELECT booking_id, hotel_name, price, booking_date
FROM hotel_bookings
WHERE booking_date >= '2026-01-01' AND booking_date < '2026-04-01';
```

**Results (fill in after running on your machine):**

| | Plan type | Execution time |
|---|---|---|
| Without index | Seq Scan | ___ ms |
| With index | Index Scan / Bitmap Index Scan | ___ ms |

> With only ~20,000 rows PostgreSQL may still choose a sequential scan, because reading the whole small table is cheap -- the query planner is making the right call, not a wrong one. The benefit of an index grows with table size. To see a clearer difference, temporarily set `NUM_RECORDS` in `generate_data.py` to a larger value (e.g. 500,000), regenerate, re-run the pipeline, and repeat the test.

### Other optimization decisions
* **Batched inserts** with `execute_values` instead of row-by-row inserts.
* **`ON CONFLICT DO NOTHING`** makes loading idempotent without a separate existence check.
* **Constraints in the database** (`CHECK`, `NOT NULL`, primary key) protect data quality even if data arrives from another source in future.
* **Correct data types** (`NUMERIC` for money, `DATE` for dates) let PostgreSQL store data compactly and compare it efficiently.
* **Indexes only where queries need them** -- every extra index slows down inserts and uses disk space, so each index above matches a specific query.

## AWS S3 integration and IAM

Each pipeline run uploads three files to S3 (`src/s3_utils.py`, called from `run_pipeline.py`):

```
s3://<bucket>/raw/<YYYY-MM-DD>/hotel_bookings.csv                    # untouched source copy
s3://<bucket>/processed/<YYYY-MM-DD>/hotel_bookings_cleaned.csv      # cleaned output
s3://<bucket>/rejected/<YYYY-MM-DD>/rejected_records.csv             # rejected rows + reasons
```

This satisfies **storing the raw dataset before processing** and **storing the cleaned output** (two of the three allowed options).

**Security requirements**
* **Environment variables only.** `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION` and `S3_BUCKET` are loaded from `.env` (git-ignored) via `python-dotenv`. `boto3` reads the access key and secret from the environment automatically -- they never appear in code. `.env.example` in the repo holds only placeholder values.
* **Least-privilege IAM.** The pipeline authenticates as a dedicated IAM user (`etl-pipeline-user`) with no console access and only the policy in `docs/iam_policy.json`:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["s3:PutObject", "s3:GetObject"],
      "Resource": "arn:aws:s3:::YOUR-BUCKET-NAME/*"
    },
    {
      "Effect": "Allow",
      "Action": ["s3:ListBucket"],
      "Resource": "arn:aws:s3:::YOUR-BUCKET-NAME"
    }
  ]
}
```

It can read and write objects in **one bucket only**. It cannot list other buckets, delete objects, or touch any other AWS service -- calling `list_buckets()` with these credentials returns `AccessDenied`, which proves the restriction (demonstrated in the video).
* **Bucket hardening:** *Block all public access* is on, and objects are encrypted at rest (SSE-S3 / AES-256) via `ExtraArgs={"ServerSideEncryption": "AES256"}` in `s3_utils.py`.
* **Failure handling:** if an upload fails, the error is logged and the function returns `None`; the pipeline continues, so an S3 outage does not block the database load.

## Scalability and architecture thinking

### Scaling to 1 million+ records
* **Read in chunks.** Use `pd.read_csv(chunksize=100_000)` so memory stays flat, and process and load chunk by chunk instead of holding the whole file in memory.
* **Vectorise validation.** `validate_data()` currently loops row by row with `iterrows()`, which is fine for 20k rows but slow at millions. Replace it with vectorised pandas boolean masks that check all rows at once (similar to how `remove_duplicates()` already works).
* **Use `COPY` for loading.** PostgreSQL's `COPY` (via `cursor.copy_expert`) is typically many times faster than repeated `INSERT`s. Load into a **staging table** first, then run one set-based `INSERT ... SELECT ... ON CONFLICT DO NOTHING` into the final table.
* **Read from S3.** Store the raw file in S3 and have the pipeline read from there, so it can run on any machine (EC2, ECS, Lambda) rather than only locally.
* **Beyond ~10-100 million rows:** move the transform step to **PySpark / AWS Glue**, store cleaned data as **Parquet** in S3 (columnar and compressed), and query it with **Athena** or load it into a warehouse such as Redshift.

### Scheduling
* **Simple option -- cron:** run the pipeline every night, e.g.
  ```
  0 2 * * * cd /app/business-etl-pipeline && venv/bin/python run_pipeline.py >> logs/cron.log 2>&1
  ```
  On Windows, Task Scheduler serves the same purpose.
* **Production option -- Apache Airflow:** one DAG with dependent tasks
  `extract >> transform >> validate >> load >> upload_to_s3`, each with retries, failure alerting, and a visible run history. In AWS this could equally be an EventBridge schedule (or an S3 "new file" event) triggering an ECS task or Lambda function.

### Partitioning and indexing strategy as data grows
* **Partition `hotel_bookings` by `booking_date`** (monthly or yearly range partitions). Queries with a date filter then read only the relevant partitions (partition pruning), and old partitions can be archived or dropped cheaply.
* **Use a BRIN index on `booking_date`** instead of a B-tree once the table is huge and naturally ordered by date -- it is tiny and fast for range scans on that kind of data.
* **Keep only indexes that queries actually use** (check `pg_stat_user_indexes` / `pg_stat_statements`) and drop the rest, since every index slows down writes.
* **Materialized views** for heavy dashboards (monthly revenue, revenue per hotel), refreshed after each load.
* **Read replicas** for reporting, so analytical queries don't compete with the load process.
* **Normalise into a star schema** as it grows: `dim_hotel`, `dim_customer`, `dim_country`, and a `fact_bookings` table.

### Failure handling
| Failure | Handling |
|---|---|
| Bad or invalid rows | never crash the pipeline; written to `rejected_records.csv` with the reason |
| Duplicate data or re-runs | `ON CONFLICT DO NOTHING` makes loads idempotent, so a failed run can simply be re-run |
| Database error mid-load | single transaction: nothing is committed, so there's no half-loaded data |
| S3 upload failure | logged; does not stop the database load |
| Production additions | automatic retries with exponential backoff (Airflow or `tenacity`), alerts to email/Slack/CloudWatch, an audit table recording each run (rows extracted / rejected / loaded, status), a dead-letter folder in S3 for unreadable files, and monitoring of the rejection rate (a sudden spike means the source changed) |


