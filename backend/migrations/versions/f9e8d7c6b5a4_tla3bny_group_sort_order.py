"""Add tla3bny_groups.sort_order (admin-controlled group order).

The tla3bny standings tables and the fixtures group filter order by this (then
id), so the admin's up/down arrangement is what everyone sees. Backfilled
sequentially per stage in id order, so existing groups keep their current
arrangement. Mirrors competition_groups.sort_order (c7d8e9f0a1b2).

Idempotent: guarded by a column-existence check.

Revision ID: f9e8d7c6b5a4
Revises: bb2233445566
Create Date: 2026-09-10
"""
from collections import defaultdict

from alembic import op
import sqlalchemy as sa

revision = 'f9e8d7c6b5a4'
down_revision = 'bb2233445566'
branch_labels = None
depends_on = None


def _has_column(table: str, column: str) -> bool:
    insp = sa.inspect(op.get_bind())
    return column in {c['name'] for c in insp.get_columns(table)}


def upgrade():
    if _has_column('tla3bny_groups', 'sort_order'):
        return
    op.add_column('tla3bny_groups',
                  sa.Column('sort_order', sa.SmallInteger(), nullable=False,
                            server_default='0'))
    # Backfill: sequential per stage, in id order, so the current arrangement is
    # preserved and each group has a distinct order to swap against.
    conn = op.get_bind()
    rows = conn.execute(sa.text(
        "SELECT id, stage_id FROM tla3bny_groups ORDER BY stage_id, id"
    )).fetchall()
    seq: dict = defaultdict(int)
    for r in rows:
        conn.execute(
            sa.text("UPDATE tla3bny_groups SET sort_order = :o WHERE id = :id"),
            {"o": seq[r.stage_id], "id": r.id},
        )
        seq[r.stage_id] += 1


def downgrade():
    if _has_column('tla3bny_groups', 'sort_order'):
        op.drop_column('tla3bny_groups', 'sort_order')
