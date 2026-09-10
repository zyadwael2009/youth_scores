"""Add admin-only phone + country code to players and coaches.

So the admin can reach a player's family (or a coach) over WhatsApp without
saving every contact on their own phone. `phone` is the local number as
entered; `phone_country_code` is the calling code (e.g. "20" for Egypt) the
frontend prepends to build the wa.me link. Both are admin-only — they ride
only on the manage roster/coach DTOs, never on any public serializer.

Idempotent: each column is guarded by an existence check.

Revision ID: e7f8a9b0c1d2
Revises: f9e8d7c6b5a4
Create Date: 2026-09-10
"""
from alembic import op
import sqlalchemy as sa

revision = 'e7f8a9b0c1d2'
down_revision = 'f9e8d7c6b5a4'
branch_labels = None
depends_on = None

_TABLES = ('players', 'coaches')


def _cols(table: str) -> set[str]:
    return {c['name'] for c in sa.inspect(op.get_bind()).get_columns(table)}


def upgrade():
    for table in _TABLES:
        have = _cols(table)
        if 'phone' not in have:
            op.add_column(table, sa.Column('phone', sa.String(length=30), nullable=True))
        if 'phone_country_code' not in have:
            op.add_column(table, sa.Column('phone_country_code', sa.String(length=6), nullable=True))


def downgrade():
    for table in _TABLES:
        have = _cols(table)
        if 'phone_country_code' in have:
            op.drop_column(table, 'phone_country_code')
        if 'phone' in have:
            op.drop_column(table, 'phone')
