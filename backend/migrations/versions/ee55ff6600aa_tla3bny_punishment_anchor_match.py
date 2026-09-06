"""Anchor a player match ban to the match it starts after.

Adds tla3bny_punishments.match_id (nullable FK -> tla3bny_matches, SET NULL). For a
player match ban it records the offense match (the team's latest finished match
when the ban was recorded), so the "matches served" count is derived from a fixed
point in the team's fixture order instead of comparing a UTC timestamp to local
match dates. NULL keeps the old date-based fallback (legacy rows, or a ban issued
before the team had played).

Idempotent: guarded by a column-existence check.

Revision ID: ee55ff6600aa
Revises: dd44ee55ff66
Create Date: 2026-09-06
"""
from alembic import op
import sqlalchemy as sa

revision = 'ee55ff6600aa'
down_revision = 'dd44ee55ff66'
branch_labels = None
depends_on = None

_TABLE = 'tla3bny_punishments'


def _has_column(column: str) -> bool:
    return column in {c['name'] for c in sa.inspect(op.get_bind()).get_columns(_TABLE)}


def upgrade():
    if not _has_column('match_id'):
        op.add_column(_TABLE, sa.Column(
            'match_id', sa.Integer(),
            sa.ForeignKey('tla3bny_matches.id', ondelete='SET NULL'),
            nullable=True,
        ))


def downgrade():
    if _has_column('match_id'):
        op.drop_column(_TABLE, 'match_id')
