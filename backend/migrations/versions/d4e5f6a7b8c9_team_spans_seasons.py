"""teams span seasons; point deduction moves to the competition entry

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-07-20

A team is a club's squad for one age group. The age group is a birth year, so
the 2009 side is the same squad season after season — it is the players and
staff that turn over, and those already carry their own dates. season_id forced
a fresh row per season, which would have split one squad's history in two.

The point deduction moves with that: a penalty belongs to the competition it
was issued in, so it must not follow the team into next season. Existing values
are copied onto every competition entry the team holds before the old column
goes, so no standings change.

Safe to apply only while each (club, age group) has a single team row; with one
season imported that is already true, and the new unique constraint keeps it so.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd4e5f6a7b8c9'
down_revision = 'c3d4e5f6a7b8'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('competition_teams', schema=None) as batch_op:
        batch_op.add_column(sa.Column('point_deduction', sa.SmallInteger(),
                                      nullable=False, server_default='0'))

    # Carry each team's deduction onto its competition entries before it is lost.
    op.execute("""
        UPDATE competition_teams
           SET point_deduction = (
                 SELECT t.point_deduction FROM teams t WHERE t.id = competition_teams.team_id
               )
         WHERE EXISTS (
                 SELECT 1 FROM teams t
                  WHERE t.id = competition_teams.team_id AND t.point_deduction > 0
               )
    """)

    with op.batch_alter_table('competition_teams', schema=None) as batch_op:
        batch_op.create_check_constraint('ck_competition_team_deduction',
                                         'point_deduction >= 0')

    # Batch mode rebuilds the table, carrying every existing constraint into the
    # new definition — including the CHECK on point_deduction, which would then
    # reference a column that is no longer there. It has to go in the same block.
    with op.batch_alter_table('teams', schema=None) as batch_op:
        # The logical name; the metadata naming convention expands it to
        # ck_teams_ck_team_point_deduction, so passing that expanded form here
        # would get it expanded a second time.
        batch_op.drop_constraint('ck_team_point_deduction', type_='check')
        batch_op.drop_index('ix_teams_club_age_season')
        batch_op.drop_column('season_id')
        batch_op.drop_column('point_deduction')
        batch_op.create_unique_constraint('uq_team_club_age', ['club_id', 'age_group_id'])


def downgrade():
    # season_id cannot be recovered once dropped; the active season is the only
    # sensible value to put back, which is what the data had.
    with op.batch_alter_table('teams', schema=None) as batch_op:
        batch_op.drop_constraint('uq_team_club_age', type_='unique')
        batch_op.add_column(sa.Column('point_deduction', sa.SmallInteger(),
                                      nullable=False, server_default='0'))
        batch_op.add_column(sa.Column('season_id', sa.Integer(), nullable=True))

    op.execute("""
        UPDATE teams SET season_id = (
            SELECT id FROM seasons ORDER BY is_active DESC, start_date DESC LIMIT 1
        )
    """)
    op.execute("""
        UPDATE teams SET point_deduction = COALESCE((
            SELECT MAX(ct.point_deduction) FROM competition_teams ct
             WHERE ct.team_id = teams.id
        ), 0)
    """)

    with op.batch_alter_table('teams', schema=None) as batch_op:
        batch_op.create_index('ix_teams_club_age_season',
                              ['club_id', 'age_group_id', 'season_id'])

    with op.batch_alter_table('competition_teams', schema=None) as batch_op:
        batch_op.drop_constraint('ck_competition_team_deduction', type_='check')
        batch_op.drop_column('point_deduction')
