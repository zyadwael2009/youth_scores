"""Add hot-path indexes for tla3bny reads.

* tla3bny_player_teams had NO indexes — it grows with every membership and is
  scanned by current_membership() and the guest-eligibility lookup. Add
  (team_id, end_date) and (player_id).
* Add (competition_id, competition_age_id, status) on tla3bny_matches for the
  sub-competition read paths (standings / analysis / feed scoped by competition_age).

Idempotent: guarded by index-existence checks.

Revision ID: aabb1122cc33
Revises: ff6600aabb11
Create Date: 2026-09-07
"""
from alembic import op
import sqlalchemy as sa

revision = 'aabb1122cc33'
down_revision = 'ff6600aabb11'
branch_labels = None
depends_on = None

_INDEXES = [
    ("ix_tla3bny_player_teams_team_end", "tla3bny_player_teams", ["team_id", "end_date"]),
    ("ix_tla3bny_player_teams_player", "tla3bny_player_teams", ["player_id"]),
    ("ix_tla3bny_matches_comp_cage_status", "tla3bny_matches",
     ["competition_id", "competition_age_id", "status"]),
]


def _has_index(table: str, name: str) -> bool:
    insp = sa.inspect(op.get_bind())
    return name in {ix["name"] for ix in insp.get_indexes(table)}


def upgrade():
    for name, table, cols in _INDEXES:
        if not _has_index(table, name):
            op.create_index(name, table, cols)


def downgrade():
    for name, table, _cols in _INDEXES:
        if _has_index(table, name):
            op.drop_index(name, table_name=table)
