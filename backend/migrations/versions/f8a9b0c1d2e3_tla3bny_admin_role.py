"""Add tla3bny_competition_admins.role (collaborator | data_entry).

"collaborator" (default) holds every organizer permission except managing the
roster (owner-only); "data_entry" may only enter match data and — if can_chat is
set — chat, and receives no notifications. Existing organizers are backfilled to
"collaborator" so their access is unchanged.

Idempotent: guarded by a column-existence check.

Revision ID: f8a9b0c1d2e3
Revises: e7f8a9b0c1d2
Create Date: 2026-09-12
"""
from alembic import op
import sqlalchemy as sa

revision = 'f8a9b0c1d2e3'
down_revision = 'e7f8a9b0c1d2'
branch_labels = None
depends_on = None

_TABLE = 'tla3bny_competition_admins'
_COL = 'role'


def _has_column(table: str, column: str) -> bool:
    return column in {c['name'] for c in sa.inspect(op.get_bind()).get_columns(table)}


def upgrade():
    if _has_column(_TABLE, _COL):
        return
    op.add_column(_TABLE, sa.Column(
        _COL, sa.String(24), nullable=False, server_default='collaborator'))
    # Existing organizers keep full access (collaborators).
    op.execute(f"UPDATE {_TABLE} SET {_COL} = 'collaborator'")


def downgrade():
    if _has_column(_TABLE, _COL):
        op.drop_column(_TABLE, _COL)
