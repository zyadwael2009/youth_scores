"""Add tla3bny_matches.finished_at — the immutable UTC moment a match first finished.

Gives the match-ban logic a stable chronological order that doesn't drift when the
stopwatch / score edits / rescheduling bump ``updated_at``. Existing finished rows are
backfilled from ``updated_at`` (the best available proxy at migration time); the value
is frozen afterwards.

Idempotent: guarded by a column-existence check.

Revision ID: ff6600aabb11
Revises: ee55ff6600aa
Create Date: 2026-09-06
"""
from alembic import op
import sqlalchemy as sa

revision = 'ff6600aabb11'
down_revision = 'ee55ff6600aa'
branch_labels = None
depends_on = None

_TABLE = 'tla3bny_matches'


def _has_column(column: str) -> bool:
    return column in {c['name'] for c in sa.inspect(op.get_bind()).get_columns(_TABLE)}


def upgrade():
    if not _has_column('finished_at'):
        op.add_column(_TABLE, sa.Column('finished_at', sa.DateTime(), nullable=True))
        # Best-effort backfill for matches already finished: updated_at ~= when the
        # result was saved. Frozen from here on (the app only sets it once).
        op.execute(
            "UPDATE tla3bny_matches SET finished_at = updated_at "
            "WHERE status IN ('finished', 'completed') AND finished_at IS NULL"
        )


def downgrade():
    if _has_column('finished_at'):
        op.drop_column(_TABLE, 'finished_at')
