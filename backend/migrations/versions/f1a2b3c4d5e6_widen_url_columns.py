"""widen ads.location_url and venues.url to 1024

Google-Maps share links run past 512 chars. SQLite ignores VARCHAR length so it
never mattered there, but MySQL enforces it (err 1406 Data too long) — needed
for the move to Railway MySQL.

Revision ID: f1a2b3c4d5e6
Revises: 4d5c00003416
Create Date: 2026-07-24
"""
from alembic import op
import sqlalchemy as sa


revision = 'f1a2b3c4d5e6'
down_revision = '4d5c00003416'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('venues', schema=None) as batch_op:
        batch_op.alter_column('url',
                              existing_type=sa.String(length=512),
                              type_=sa.String(length=1024),
                              existing_nullable=True)
    with op.batch_alter_table('ads', schema=None) as batch_op:
        batch_op.alter_column('location_url',
                              existing_type=sa.String(length=512),
                              type_=sa.String(length=1024),
                              existing_nullable=True)


def downgrade():
    with op.batch_alter_table('ads', schema=None) as batch_op:
        batch_op.alter_column('location_url',
                              existing_type=sa.String(length=1024),
                              type_=sa.String(length=512),
                              existing_nullable=True)
    with op.batch_alter_table('venues', schema=None) as batch_op:
        batch_op.alter_column('url',
                              existing_type=sa.String(length=1024),
                              type_=sa.String(length=512),
                              existing_nullable=True)
