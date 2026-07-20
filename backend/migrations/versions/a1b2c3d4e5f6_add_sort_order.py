"""add sort_order to team_coaches, club_staff, player_teams

Revision ID: a1b2c3d4e5f6
Revises: d478974a3aab
Create Date: 2026-07-19

Manual display order for the admin reorder controls. Defaults to 0 for
existing rows; the reorder endpoints assign 0..n once a list is arranged.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = 'd478974a3aab'
branch_labels = None
depends_on = None

_TABLES = ('team_coaches', 'club_staff', 'player_teams')


def upgrade():
    for tbl in _TABLES:
        with op.batch_alter_table(tbl, schema=None) as batch_op:
            batch_op.add_column(
                sa.Column('sort_order', sa.SmallInteger(), nullable=False, server_default='0')
            )


def downgrade():
    for tbl in _TABLES:
        with op.batch_alter_table(tbl, schema=None) as batch_op:
            batch_op.drop_column('sort_order')
