"""Add tla3bny_matches.lineup_reminder_sent_at (the "submit your lineup" reminder guard).

Stamped when the periodic reminder task has pinged a match's teams, so a team is never
reminded twice.

Idempotent: guarded by a column-existence check.

Revision ID: bb2233445566
Revises: aabb1122cc33
Create Date: 2026-09-07
"""
from alembic import op
import sqlalchemy as sa

revision = 'bb2233445566'
down_revision = 'aabb1122cc33'
branch_labels = None
depends_on = None

_TABLE = 'tla3bny_matches'


def _has_column(column: str) -> bool:
    return column in {c['name'] for c in sa.inspect(op.get_bind()).get_columns(_TABLE)}


def upgrade():
    if not _has_column('lineup_reminder_sent_at'):
        op.add_column(_TABLE, sa.Column('lineup_reminder_sent_at', sa.DateTime(), nullable=True))


def downgrade():
    if _has_column('lineup_reminder_sent_at'):
        op.drop_column(_TABLE, 'lineup_reminder_sent_at')
