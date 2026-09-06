"""Add the live match stopwatch to tla3bny_matches.

An organizer runs the match clock (never public). timer_started_at is the server
time the current running segment began (NULL = paused/stopped); timer_elapsed is
the seconds banked before it.

Idempotent: guarded by column-existence checks.

Revision ID: dd44ee55ff66
Revises: cc33dd44ee55
Create Date: 2026-09-06
"""
from alembic import op
import sqlalchemy as sa

revision = 'dd44ee55ff66'
down_revision = 'cc33dd44ee55'
branch_labels = None
depends_on = None

_TABLE = 'tla3bny_matches'


def _has_column(column: str) -> bool:
    return column in {c['name'] for c in sa.inspect(op.get_bind()).get_columns(_TABLE)}


def upgrade():
    if not _has_column('timer_started_at'):
        op.add_column(_TABLE, sa.Column('timer_started_at', sa.DateTime(), nullable=True))
    if not _has_column('timer_elapsed'):
        op.add_column(_TABLE, sa.Column('timer_elapsed', sa.Integer(), nullable=False,
                                        server_default='0'))


def downgrade():
    if _has_column('timer_elapsed'):
        op.drop_column(_TABLE, 'timer_elapsed')
    if _has_column('timer_started_at'):
        op.drop_column(_TABLE, 'timer_started_at')
