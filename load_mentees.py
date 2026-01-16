"""
load_mentees.py

Load mentee intake data from a CSV export (online form) into PostgreSQL.

- Reads DB_URL from .env
- Reads mentee CSV from MENTEE_CSV_PATH env var (optional)
  default: mentee_form_responses.csv (project root)
- Handles empty CSV gracefully (no crash)
- Stores raw submissions as JSONB (deduped by hash)
- Inserts normalized mentee rows

Run:
  ./.venv/bin/python load_mentees.py
"""

from __future__ import annotations

import hashlib
import json
import os
from typing import Any, Dict

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine


# ----------------------------
# Config
# ----------------------------

DEFAULT_CSV_PATH = "mentee_form_responses.csv"

# Update these keys to match YOUR actual CSV headers if they differ.
# Google Forms usually exports headers like these.
COLUMN_MAP = {
    "Timestamp": "submitted_at",
    "First Name": "first_name",
    "Last Name": "last_name",
    "Guardian Name": "guardian_name",
    "Guardian Email": "guardian_email",
    "Phone": "phone",
    "School": "school",
    "Grade": "grade",
    "Interests": "interests",
}

REQUIRED_FIELDS = ["submitted_at", "first_name", "last_name"]


# ----------------------------
# Helpers
# ----------------------------

def get_engine() -> Engine:
    # Force loading .env from the project root
    load_dotenv(dotenv_path=".env")

    db_url = os.getenv("DB_URL")
    if not db_url:
        raise ValueError("Missing DB_URL in .env")

    return create_engine(db_url, pool_pre_ping=True)


def stable_hash(payload: Dict[str, Any]) -> str:
    dumped = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(dumped.encode("utf-8")).hexdigest()


def row_to_payload(row: pd.Series) -> Dict[str, Any]:
    payload: Dict[str, Any] = {}
    for k, v in row.items():
        if pd.isna(v):
            continue
        if isinstance(v, pd.Timestamp):
            payload[k] = v.to_pydatetime().isoformat()
        else:
            payload[k] = str(v).strip()
    return payload


def ensure_tables_exist(engine: Engine) -> None:
    with engine.connect() as conn:
        res = conn.execute(
            text("""
                SELECT
                  to_regclass('public.mentees') AS mentees,
                  to_regclass('public.mentee_intake_submissions') AS subs;
            """)
        ).mappings().one()

        if res["mentees"] is None or res["subs"] is None:
            raise RuntimeError(
                "Required tables not found. Run schema.sql first (mentees + mentee_intake_submissions)."
            )


# ----------------------------
# Main
# ----------------------------

def main() -> None:
    engine = get_engine()
    ensure_tables_exist(engine)

    csv_path = os.getenv("MENTEE_CSV_PATH", DEFAULT_CSV_PATH)

    # Handle missing file
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"CSV not found: {csv_path}")

    # Handle completely empty file (0 bytes)
    if os.path.getsize(csv_path) == 0:
        print(f"⚠️ {csv_path} is empty — no mentee submissions to load yet.")
        return

    # Read CSV
    try:
        df = pd.read_csv(csv_path)
    except pd.errors.EmptyDataError:
        # Handles weird edge cases where file exists but pandas sees no columns
        print(f"⚠️ {csv_path} has no readable columns — no mentee submissions to load yet.")
        return

    # Handle header-only (no data rows)
    if df.empty:
        print(f"⚠️ {csv_path} has headers but no rows — nothing to load yet.")
        return

    # Rename columns to normalized names
    df = df.rename(columns={c: COLUMN_MAP.get(c, c) for c in df.columns})

    # Parse submitted_at
    if "submitted_at" in df.columns:
        df["submitted_at"] = pd.to_datetime(df["submitted_at"], errors="coerce")

    # Trim strings
    for col in ["first_name", "last_name", "guardian_name", "guardian_email", "phone", "school", "grade", "interests"]:
        if col in df.columns:
            df[col] = df[col].astype("string").str.strip()

    # Lowercase guardian_email for consistency
    if "guardian_email" in df.columns:
        df["guardian_email"] = df["guardian_email"].str.lower()

    rows_read = len(df)
    skipped_missing_required = 0
    raw_inserted = 0
    mentees_inserted = 0

    with engine.begin() as conn:
        # Add dedupe column (safe if already exists)
        conn.execute(text("""
            ALTER TABLE mentee_intake_submissions
            ADD COLUMN IF NOT EXISTS submission_hash TEXT UNIQUE;
        """))

        for _, row in df.iterrows():
            # Validate required fields
            missing = []
            for f in REQUIRED_FIELDS:
                if f not in df.columns or pd.isna(row.get(f)):
                    missing.append(f)

            if missing:
                skipped_missing_required += 1
                continue

            payload = row_to_payload(row)
            shash = stable_hash(payload)

            # 1) Insert raw submission (deduped)
            r = conn.execute(
                text("""
                    INSERT INTO mentee_intake_submissions (submitted_at, raw_payload, source, submission_hash)
                    VALUES (:submitted_at, :raw_payload::jsonb, :source, :submission_hash)
                    ON CONFLICT (submission_hash) DO NOTHING
                """),
                {
                    "submitted_at": row["submitted_at"].to_pydatetime()
                    if isinstance(row["submitted_at"], pd.Timestamp)
                    else row["submitted_at"],
                    "raw_payload": json.dumps(payload),
                    "source": "csv_export",
                    "submission_hash": shash,
                },
            )
            if r.rowcount == 1:
                raw_inserted += 1

            # 2) Insert normalized mentee row
            conn.execute(
                text("""
                    INSERT INTO mentees
                    (first_name, last_name, guardian_name, guardian_email, phone, school, grade, interests)
                    VALUES (:first_name, :last_name, :guardian_name, :guardian_email, :phone, :school, :grade, :interests)
                """),
                {
                    "first_name": payload.get("first_name"),
                    "last_name": payload.get("last_name"),
                    "guardian_name": payload.get("guardian_name"),
                    "guardian_email": payload.get("guardian_email"),
                    "phone": payload.get("phone"),
                    "school": payload.get("school"),
                    "grade": payload.get("grade"),
                    "interests": payload.get("interests"),
                },
            )
            mentees_inserted += 1

    print("\n✅ Mentee intake load complete")
    print(f"  CSV path:                       {csv_path}")
    print(f"  Rows read:                      {rows_read}")
    print(f"  Raw submissions inserted:       {raw_inserted}")
    print(f"  Mentees inserted:               {mentees_inserted}")
    print(f"  Rows skipped (missing required): {skipped_missing_required}\n")


if __name__ == "__main__":
    main()

