"""add carries_points to stages

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-07-20

Marks whether a stage's table continues from the earlier stages or restarts
from zero. Defaults to true, which is exactly how every existing table is
already computed, so applying this changes no standings.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b2c3d4e5f6a7'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('stages', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('carries_points', sa.Boolean(), nullable=False,
                      server_default=sa.true())
        )


def downgrade():
    with op.batch_alter_table('stages', schema=None) as batch_op:
        batch_op.drop_column('carries_points')
