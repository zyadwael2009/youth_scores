"""Copy all rows from a SQLite database into another SQLAlchemy target
(e.g. Railway MySQL), table by table, using the app's own metadata so column
types convert correctly (dates, booleans, Arabic text).

The TARGET SCHEMA MUST ALREADY EXIST — create it first by running
`flask db upgrade` against the target, so Alembic builds MySQL-correct DDL and
sets alembic_version to the current head. This script only copies data.

Usage (run from the backend/ directory):

    SOURCE_URL="sqlite:///instance/youthscores.rehearsal.db" \
    TARGET_URL="mysql://root:PASS@HOST:PORT/railway" \
    python -m scripts.sqlite_to_mysql

TARGET_URL accepts Railway's raw mysql://… (it is normalised to
mysql+pymysql://…?charset=utf8mb4 automatically).
"""

import os
import sys

from sqlalchemy import create_engine, insert, select, text

from app.config import _normalize_db_url
from app.extensions import db
import app.models  # noqa: F401  — registers every table on db.metadata


def main() -> None:
    source_url = os.environ.get("SOURCE_URL")
    target_url = _normalize_db_url(os.environ.get("TARGET_URL"))
    if not source_url or not target_url:
        sys.exit("Set SOURCE_URL and TARGET_URL environment variables.")

    src = create_engine(source_url)
    tgt = create_engine(target_url)
    is_mysql = tgt.dialect.name == "mysql"

    tables = db.metadata.sorted_tables  # parent tables first (FK order)
    print(f"Copying {len(tables)} tables: {source_url}  ->  {tgt.dialect.name}\n")

    total = 0
    with src.connect() as s, tgt.begin() as t:
        # Order handles FKs, but disabling checks also tolerates any cycle and
        # lets a table load before a self-referential row's target exists.
        if is_mysql:
            t.execute(text("SET FOREIGN_KEY_CHECKS=0"))
        for table in tables:
            existing = t.execute(select(table).limit(1)).first()
            if existing is not None:
                print(f"  ! {table.name}: target not empty — skipping")
                continue
            rows = [dict(r._mapping) for r in s.execute(select(table))]
            if rows:
                t.execute(insert(table), rows)
            total += len(rows)
            print(f"  - {table.name}: {len(rows)}")
        if is_mysql:
            t.execute(text("SET FOREIGN_KEY_CHECKS=1"))

    print(f"\nDone. {total} rows copied into {len(tables)} tables.")


if __name__ == "__main__":
    main()
