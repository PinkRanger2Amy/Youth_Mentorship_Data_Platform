"""
match_mentees.py

Generate mentor ↔ mentee matches based on shared interests (simple scoring).
Writes results to matches table using UPSERT.

Run:
  ./.venv/bin/python match_mentees.py
"""

from __future__ import annotations

import os
import re
from typing import List, Set, Tuple

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text


def tokenize(s: str | None) -> Set[str]:
    if not s:
        return set()
    # split on commas, slashes, semicolons, and whitespace
    parts = re.split(r"[,/;|\n\r\t ]+", str(s).lower())
    return {p.strip() for p in parts if p.strip()}


def score_pair(mentor_row, mentee_row) -> Tuple[int, str]:
    m_interests = tokenize(mentor_row.get("interests"))
    t_interests = tokenize(mentee_row.get("interests"))

    overlap = sorted(m_interests.intersection(t_interests))
    score = len(overlap) * 10  # 10 points per shared interest

    # small bonus if mentor availability exists (placeholder for later)
    if mentor_row.get("availability"):
        score += 2

    reason = "shared_interests=" + (", ".join(overlap) if overlap else "none")
    return score, reason


def main() -> None:
    load_dotenv(dotenv_path=".env")
    db_url = os.getenv("DB_URL")
    if not db_url:
        raise ValueError("Missing DB_URL in .env")

    engine = create_engine(db_url, pool_pre_ping=True)

    with engine.connect() as conn:
        mentors = pd.read_sql(text("SELECT * FROM mentors;"), conn)
        mentees = pd.read_sql(text("SELECT * FROM mentees;"), conn)

    if mentors.empty:
        print("⚠️ No mentors found. Run load_intake.py first.")
        return

    if mentees.empty:
        print("⚠️ No mentees found yet. Matching skipped (this is OK).")
        return

    # Compute top matches per mentee
    rows_to_upsert = []
    for _, mentee in mentees.iterrows():
        scored: List[Tuple[int, int, str]] = []
        for _, mentor in mentors.iterrows():
            score, reason = score_pair(mentor, mentee)
            scored.append((score, int(mentor["mentor_id"]), reason))

        # Keep top 3 matches (you can change this)
        top = sorted(scored, key=lambda x: x[0], reverse=True)[:3]
        for score, mentor_id, reason in top:
            rows_to_upsert.append(
                {
                    "mentor_id": mentor_id,
                    "mentee_id": int(mentee["mentee_id"]),
                    "match_score": int(score),
                    "match_reason": reason,
                }
            )

    # Write to DB (upsert)
    upsert_sql = text("""
        INSERT INTO matches (mentor_id, mentee_id, match_score, match_reason, updated_at)
        VALUES (:mentor_id, :mentee_id, :match_score, :match_reason, NOW())
        ON CONFLICT (mentor_id, mentee_id)
        DO UPDATE SET
          match_score = EXCLUDED.match_score,
          match_reason = EXCLUDED.match_reason,
          updated_at = NOW();
    """)

    with engine.begin() as conn:
        for r in rows_to_upsert:
            conn.execute(upsert_sql, r)

    print("✅ Matching complete")
    print(f"  Mentors: {len(mentors)}")
    print(f"  Mentees: {len(mentees)}")
    print(f"  Match rows written/updated: {len(rows_to_upsert)}")


if __name__ == "__main__":
    main()
