"""drop the team academy columns

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-07-20

The team's own name_ar/name_en already override the club name for a side that
plays under different branding, and that is what the standings and fixtures
show. A separate academy field said the same thing twice, so it goes.

Nothing real is lost: the columns were added earlier today and only ever held a
single demonstration value.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e5f6a7b8c9d0'
down_revision = 'd4e5f6a7b8c9'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('teams', schema=None) as batch_op:
        batch_op.drop_column('academy_ar')
        batch_op.drop_column('academy_en')


def downgrade():
    with op.batch_alter_table('teams', schema=None) as batch_op:
        batch_op.add_column(sa.Column('academy_en', sa.String(length=160), nullable=True))
        batch_op.add_column(sa.Column('academy_ar', sa.String(length=160), nullable=True))
