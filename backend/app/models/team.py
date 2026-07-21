from datetime import date

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import codes
from app.models.base import TimestampMixin, code_enum, db


class Team(TimestampMixin, db.Model):
    """A club's squad for one age group, across every season it plays.

    A club fielding 2009 through 2013 sides has one Club row and five Team rows.
    The second name a side plays under (an academy's or sponsor's branding) is
    not here: it can differ from one competition to the next, so it lives on the
    CompetitionTeam entry. The club stays the legal owner via club_id.

    Deliberately not scoped to a season. The age group here is a birth year, so
    the 2009 side is the same squad from one season to the next — it is the
    players and staff that turn over, and those already carry their own start
    and end dates. Which seasons a team actually played is read from the
    competitions it entered, via CompetitionTeam.
    """

    __tablename__ = "teams"

    id: Mapped[int] = mapped_column(primary_key=True)

    club_id: Mapped[int] = mapped_column(
        sa.ForeignKey("clubs.id", ondelete="RESTRICT"), nullable=False
    )
    age_group_id: Mapped[int] = mapped_column(
        sa.ForeignKey("age_groups.id", ondelete="RESTRICT"), nullable=False
    )

    short_name_en: Mapped[str | None] = mapped_column(sa.String(40))
    short_name_ar: Mapped[str | None] = mapped_column(sa.String(40))

    # Origin key from the feed, kept so an import can be re-run without
    # duplicating rows.
    source_ref: Mapped[str | None] = mapped_column(sa.String(120), unique=True)

    club: Mapped["Club"] = relationship(back_populates="teams")
    age_group: Mapped["AgeGroup"] = relationship(back_populates="teams")
    coaches: Mapped[list["TeamCoach"]] = relationship(
        back_populates="team", cascade="all, delete-orphan"
    )
    registrations: Mapped[list["PlayerTeam"]] = relationship(
        back_populates="team", cascade="all, delete-orphan"
    )

    __table_args__ = (
        sa.UniqueConstraint("club_id", "age_group_id", name="uq_team_club_age"),
    )

    def __repr__(self) -> str:
        return f"<Team {self.id} club={self.club_id} age={self.age_group_id}>"


class TeamCoach(TimestampMixin, db.Model):
    """Historical assignment of a coach to a team. end_date NULL = current."""

    __tablename__ = "team_coaches"

    id: Mapped[int] = mapped_column(primary_key=True)

    team_id: Mapped[int] = mapped_column(
        sa.ForeignKey("teams.id", ondelete="CASCADE"), nullable=False
    )
    coach_id: Mapped[int] = mapped_column(
        sa.ForeignKey("coaches.id", ondelete="RESTRICT"), nullable=False
    )

    role_en: Mapped[str | None] = mapped_column(sa.String(80))
    role_ar: Mapped[str | None] = mapped_column(sa.String(80))
    start_date: Mapped[date] = mapped_column(sa.Date, nullable=False)
    end_date: Mapped[date | None] = mapped_column(sa.Date)

    # Manual display order (ascending). 0 = unset; reorder UI assigns 0..n.
    sort_order: Mapped[int] = mapped_column(sa.SmallInteger, nullable=False, default=0)

    team: Mapped["Team"] = relationship(back_populates="coaches")
    coach: Mapped["Coach"] = relationship(back_populates="team_roles")

    __table_args__ = (
        sa.CheckConstraint(
            "end_date IS NULL OR end_date >= start_date", name="ck_team_coach_dates"
        ),
        sa.Index("ix_team_coaches_team", "team_id"),
    )


class PlayerTeam(TimestampMixin, db.Model):
    """Player registration with a team, and the record of transfers.

    A mid-season move closes the old row with an end_date and opens a new one.
    end_date NULL = currently registered.
    """

    __tablename__ = "player_teams"

    id: Mapped[int] = mapped_column(primary_key=True)

    player_id: Mapped[int] = mapped_column(
        sa.ForeignKey("players.id", ondelete="CASCADE"), nullable=False
    )
    team_id: Mapped[int] = mapped_column(
        sa.ForeignKey("teams.id", ondelete="CASCADE"), nullable=False
    )

    shirt_number: Mapped[int | None] = mapped_column(sa.SmallInteger)
    start_date: Mapped[date] = mapped_column(sa.Date, nullable=False)
    end_date: Mapped[date | None] = mapped_column(sa.Date)
    status: Mapped[str] = mapped_column(
        code_enum(*codes.PLAYER_TEAM_STATUS), nullable=False, default="active"
    )

    # Manual display order (ascending). 0 = unset; reorder UI assigns 0..n.
    sort_order: Mapped[int] = mapped_column(sa.SmallInteger, nullable=False, default=0)

    player: Mapped["Player"] = relationship(back_populates="registrations")
    team: Mapped["Team"] = relationship(back_populates="registrations")

    __table_args__ = (
        sa.CheckConstraint(
            "end_date IS NULL OR end_date >= start_date", name="ck_player_team_dates"
        ),
        sa.Index("ix_player_teams_player", "player_id"),
        sa.Index("ix_player_teams_team", "team_id"),
    )

    @property
    def is_current(self) -> bool:
        return self.end_date is None


class ClubStaff(TimestampMixin, db.Model):
    """Administrative and technical roles in a club's youth sector."""

    __tablename__ = "club_staff"

    id: Mapped[int] = mapped_column(primary_key=True)

    club_id: Mapped[int] = mapped_column(
        sa.ForeignKey("clubs.id", ondelete="CASCADE"), nullable=False
    )
    coach_id: Mapped[int] = mapped_column(
        sa.ForeignKey("coaches.id", ondelete="RESTRICT"), nullable=False
    )

    role_en: Mapped[str | None] = mapped_column(sa.String(80))
    role_ar: Mapped[str | None] = mapped_column(sa.String(80))
    start_date: Mapped[date | None] = mapped_column(sa.Date)
    end_date: Mapped[date | None] = mapped_column(sa.Date)

    # Manual display order (ascending). 0 = unset; reorder UI assigns 0..n.
    sort_order: Mapped[int] = mapped_column(sa.SmallInteger, nullable=False, default=0)

    club: Mapped["Club"] = relationship(back_populates="staff")
    coach: Mapped["Coach"] = relationship(back_populates="club_roles")

    __table_args__ = (
        sa.CheckConstraint(
            "start_date IS NULL OR end_date IS NULL OR end_date >= start_date",
            name="ck_club_staff_dates",
        ),
    )
