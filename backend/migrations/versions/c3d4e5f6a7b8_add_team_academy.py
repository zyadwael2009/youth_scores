"""add academy name to teams

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-07-20

Records the academy running a squad for one season, where that is not the club
itself. Players register with the federation under the club, so the club keeps
the identity and this is only what the side is known by; it sits on the team
because the arrangement is per season and per age group, not per club.

Both columns are nullable and default to NULL, so existing teams are unchanged.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c3d4e5f6a7b8'
down_revision = 'b2c3d4e5f6a7'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('teams', schema=None) as batch_op:
        batch_op.add_column(sa.Column('academy_en', sa.String(length=160), nullable=True))
        batch_op.add_column(sa.Column('academy_ar', sa.String(length=160), nullable=True))


def downgrade():
    with op.batch_alter_table('teams', schema=None) as batch_op:
        batch_op.drop_column('academy_ar')
        batch_op.drop_column('academy_en')
