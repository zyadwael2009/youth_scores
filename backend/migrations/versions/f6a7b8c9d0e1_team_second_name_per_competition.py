"""the team's second name moves to the competition entry

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-07-21

The second name a side plays under (an academy's or sponsor's branding) is not a
permanent property of the squad: the same 2009 side can run under different
branding from one competition or season to the next. So it moves from the team
onto each CompetitionTeam entry, the same way point_deduction did — a property of
the entry, not of the squad.

Existing team names are copied onto every competition entry the team holds before
the old columns are dropped, so nothing on screen changes for the data as it
stands (no squad currently carries a different name across its entries).

Safe to apply only while each (club, age group) has a single team row; the
uq_team_club_age constraint already guarantees that.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f6a7b8c9d0e1'
down_revision = 'e5f6a7b8c9d0'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('competition_teams', schema=None) as batch_op:
        batch_op.add_column(sa.Column('name_en', sa.String(length=160), nullable=True))
        batch_op.add_column(sa.Column('name_ar', sa.String(length=160), nullable=True))

    # Carry each squad's second name onto its competition entries before it is
    # lost. Every entry of a team takes the team's single name.
    op.execute("""
        UPDATE competition_teams
           SET name_ar = (SELECT t.name_ar FROM teams t WHERE t.id = competition_teams.team_id),
               name_en = (SELECT t.name_en FROM teams t WHERE t.id = competition_teams.team_id)
    """)

    with op.batch_alter_table('teams', schema=None) as batch_op:
        batch_op.drop_column('name_ar')
        batch_op.drop_column('name_en')


def downgrade():
    with op.batch_alter_table('teams', schema=None) as batch_op:
        batch_op.add_column(sa.Column('name_en', sa.String(length=160), nullable=True))
        batch_op.add_column(sa.Column('name_ar', sa.String(length=160), nullable=True))

    # Put back the most recent entry's name onto the squad. Properly ordering by
    # season would need joins SQLite's correlated UPDATE cannot express cleanly;
    # the highest entry id is a good enough proxy for "most recent".
    op.execute("""
        UPDATE teams SET
            name_ar = (SELECT ct.name_ar FROM competition_teams ct
                        WHERE ct.team_id = teams.id AND ct.name_ar IS NOT NULL
                        ORDER BY ct.id DESC LIMIT 1),
            name_en = (SELECT ct.name_en FROM competition_teams ct
                        WHERE ct.team_id = teams.id AND ct.name_en IS NOT NULL
                        ORDER BY ct.id DESC LIMIT 1)
    """)

    with op.batch_alter_table('competition_teams', schema=None) as batch_op:
        batch_op.drop_column('name_ar')
        batch_op.drop_column('name_en')
