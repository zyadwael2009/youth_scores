"""make match_date nullable (TBD fixtures)

Revision ID: a7b8c9d0e1f2
Revises: f6a7b8c9d0e1
Create Date: 2026-07-23

A fixture can be confirmed before its date is set. Allowing match_date to be
NULL lets such a match be entered and shown as "غير محدد" until scheduled;
every existing row already has a date, so nothing changes for them.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a7b8c9d0e1f2'
down_revision = 'f6a7b8c9d0e1'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('matches', schema=None) as batch_op:
        batch_op.alter_column('match_date', existing_type=sa.DateTime(),
                              nullable=True)


def downgrade():
    # A NULL match_date cannot satisfy the old NOT NULL. Park undated fixtures at
    # the epoch so the constraint can be restored without dropping rows.
    op.execute("UPDATE matches SET match_date = '1970-01-01 00:00:00' "
               "WHERE match_date IS NULL")
    with op.batch_alter_table('matches', schema=None) as batch_op:
        batch_op.alter_column('match_date', existing_type=sa.DateTime(),
                              nullable=False)
