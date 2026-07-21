"""Copy every row from a source database into the app's configured database.

Used to load a local SQLite copy onto the deployed MySQL. Both must already be
at the same Alembic revision — run `flask db upgrade` on each first — then this
copies the data table by table using the app's own models, so datetimes,
booleans and JSON columns convert correctly across the two engines.

The target is wiped and replaced. Foreign-key checks are turned off for the
copy so table order and any self-reference load cleanly; tables are still
written parents-first as a belt-and-braces.

    python -m scripts.copy_db /path/to/youthscores.db            # dry run
    python -m scripts.copy_db /path/to/youthscores.db --apply

DATABASE_URL (the target) comes from the environment / .env, exactly as the app
reads it — so run this on the host whose database you want to fill.
"""
from __future__ import annotations

import os
import sys

import sqlalchemy as sa

from app import create_app
from app.extensions import db


def _set_fk(conn, on: bool) -> None:
    name = conn.dialect.name
    if name == "sqlite":
        conn.exec_driver_sql(f"PRAGMA foreign_keys = {'ON' if on else 'OFF'}")
    elif name in ("mysql", "mariadb"):
        conn.exec_driver_sql(f"SET FOREIGN_KEY_CHECKS = {1 if on else 0}")


def main(source_path: str, apply: bool) -> None:
    if not os.path.isfile(source_path):
        print(f"لا يوجد ملف: {source_path}")
        return

    app = create_app()
    with app.app_context():
        target = db.engine
        source = sa.create_engine(f"sqlite:///{os.path.abspath(source_path)}")

        # The models define the schema for both ends; both databases must match
        # it (same migration head). Ordered so parents come before children.
        tables = list(db.metadata.sorted_tables)

        print(f"source: {source_path}")
        print(f"target: {target.url}\n")

        plan = []
        with source.connect() as sc:
            for t in tables:
                n = sc.execute(sa.select(sa.func.count()).select_from(t)).scalar()
                plan.append((t, n))
                print(f"  {t.name:28} {n:>8} rows")
        print(f"\nإجمالي الصفوف: {sum(n for _, n in plan)}")

        if not apply:
            print("\nDRY RUN — لم يُكتب شيء. أضف --apply للنسخ.")
            return

        with source.connect() as sc, target.begin() as tc:
            _set_fk(tc, False)
            # Empty the target, children first.
            for t in reversed(tables):
                tc.execute(t.delete())
            # Fill it, parents first, in batches.
            for t, n in plan:
                if not n:
                    continue
                rows = [dict(r._mapping) for r in sc.execute(sa.select(t))]
                for i in range(0, len(rows), 1000):
                    tc.execute(t.insert(), rows[i:i + 1000])
                print(f"  ✓ {t.name}: {n}")
            _set_fk(tc, True)

        print("\nAPPLIED — البيانات نُسخت.")


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a != "--apply"]
    if not args:
        print(__doc__)
        sys.exit(1)
    main(args[0], apply="--apply" in sys.argv)
