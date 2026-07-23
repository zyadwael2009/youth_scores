"""tla3bny — the LeagueHub subdomain (tla3bny.youthscores.org).

A self-contained league-management subsystem ported from the standalone `ug/`
project. Everything here lives in `tla3bny_*` tables and shares nothing with the
youthscores competition data — the two are separate leagues that merely share a
database. Academies self-register and manage rosters; a league super admin
approves them, schedules matches, and records results. Standings and leaderboards
are computed per age category.

Serialization is kept on the models (as `to_dict`) rather than in a serializers
module, so this subsystem stays a single, self-contained unit.
"""

from datetime import date, datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship
from werkzeug.security import check_password_hash, generate_password_hash

from app.models import codes
from app.models.base import TimestampMixin, code_enum, db


class Tla3bnyUser(TimestampMixin, db.Model):
    """A tla3bny account: the league super admin or a registered academy.

    role="super_admin" (status "active") administers the league; role="academy"
    accounts self-register (status "pending") and are approved/rejected by the
    super admin. Academy profile columns are null for the super admin.
    """

    __tablename__ = "tla3bny_users"

    id: Mapped[int] = mapped_column(primary_key=True)

    email: Mapped[str] = mapped_column(
        sa.String(255), nullable=False, unique=True, index=True
    )
    password_hash: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    role: Mapped[str] = mapped_column(
        code_enum(*codes.TLA3BNY_USER_ROLE), nullable=False, default="academy"
    )
    status: Mapped[str] = mapped_column(
        code_enum(*codes.TLA3BNY_USER_STATUS), nullable=False, default="pending"
    )

    # Academy profile fields (null for the super admin).
    name: Mapped[str | None] = mapped_column(sa.String(255))
    logo_path: Mapped[str | None] = mapped_column(sa.String(512))
    phone: Mapped[str | None] = mapped_column(sa.String(50))
    address: Mapped[str | None] = mapped_column(sa.String(255))
    rejection_reason: Mapped[str | None] = mapped_column(sa.String(512))

    players: Mapped[list["Tla3bnyPlayer"]] = relationship(
        back_populates="academy", cascade="all, delete-orphan"
    )

    # -- password helpers ---------------------------------------------------
    def set_password(self, raw: str) -> None:
        self.password_hash = generate_password_hash(raw)

    def check_password(self, raw: str) -> bool:
        return check_password_hash(self.password_hash, raw)

    # -- serialization ------------------------------------------------------
    def to_dict(self, public: bool = False) -> dict:
        data = {
            "id": self.id,
            "name": self.name,
            "logo_path": self.logo_path,
            "role": self.role,
            "status": self.status,
        }
        if not public:
            data.update(
                {
                    "email": self.email,
                    "phone": self.phone,
                    "address": self.address,
                    "rejection_reason": self.rejection_reason,
                    "created_at": self.created_at.isoformat()
                    if self.created_at
                    else None,
                    "player_count": len(self.players),
                }
            )
        return data

    def __repr__(self) -> str:
        return f"<Tla3bnyUser {self.id} {self.role} {self.email}>"


class Tla3bnyAgeCategory(TimestampMixin, db.Model):
    __tablename__ = "tla3bny_age_categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    label: Mapped[str] = mapped_column(sa.String(50), nullable=False, unique=True)
    # How many document files each player in this category must upload.
    required_files: Mapped[int] = mapped_column(
        sa.Integer, nullable=False, default=1
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "label": self.label,
            "required_files": self.required_files,
        }

    def __repr__(self) -> str:
        return f"<Tla3bnyAgeCategory {self.id} {self.label}>"


class Tla3bnyPlayer(TimestampMixin, db.Model):
    __tablename__ = "tla3bny_players"

    id: Mapped[int] = mapped_column(primary_key=True)
    academy_id: Mapped[int] = mapped_column(
        sa.ForeignKey("tla3bny_users.id"), nullable=False
    )
    age_category_id: Mapped[int | None] = mapped_column(
        sa.ForeignKey("tla3bny_age_categories.id")
    )

    name: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    position: Mapped[str | None] = mapped_column(sa.String(50))
    sub_position: Mapped[str | None] = mapped_column(sa.String(50))
    dob: Mapped[date | None] = mapped_column(sa.Date)
    jersey_number: Mapped[int | None] = mapped_column(sa.Integer)
    photo_path: Mapped[str | None] = mapped_column(sa.String(512))
    papers_path: Mapped[str | None] = mapped_column(sa.String(512))
    # Verification workflow: pending -> approved / rejected (by super admin).
    status: Mapped[str] = mapped_column(
        code_enum(*codes.TLA3BNY_PLAYER_STATUS), nullable=False, default="pending"
    )
    rejection_reason: Mapped[str | None] = mapped_column(sa.String(512))

    academy: Mapped["Tla3bnyUser"] = relationship(back_populates="players")
    age_category: Mapped["Tla3bnyAgeCategory | None"] = relationship()
    files: Mapped[list["Tla3bnyPlayerFile"]] = relationship(
        back_populates="player", cascade="all, delete-orphan"
    )

    @property
    def required_files(self) -> int:
        return self.age_category.required_files if self.age_category else 0

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "academy_id": self.academy_id,
            "academy_name": self.academy.name if self.academy else None,
            "age_category_id": self.age_category_id,
            "age_category": self.age_category.label if self.age_category else None,
            "name": self.name,
            "position": self.position,
            "sub_position": self.sub_position,
            "dob": self.dob.isoformat() if self.dob else None,
            "jersey_number": self.jersey_number,
            "photo_path": self.photo_path,
            "papers_path": self.papers_path,
            "status": self.status,
            "rejection_reason": self.rejection_reason,
            "files": [f.to_dict() for f in self.files],
            "file_count": len(self.files),
            "required_files": self.required_files,
        }

    def __repr__(self) -> str:
        return f"<Tla3bnyPlayer {self.id} {self.name}>"


class Tla3bnyPlayerFile(TimestampMixin, db.Model):
    __tablename__ = "tla3bny_player_files"

    id: Mapped[int] = mapped_column(primary_key=True)
    player_id: Mapped[int] = mapped_column(
        sa.ForeignKey("tla3bny_players.id"), nullable=False
    )
    file_path: Mapped[str] = mapped_column(sa.String(512), nullable=False)
    original_name: Mapped[str | None] = mapped_column(sa.String(255))

    player: Mapped["Tla3bnyPlayer"] = relationship(back_populates="files")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "file_path": self.file_path,
            "original_name": self.original_name,
        }


class Tla3bnyMatch(TimestampMixin, db.Model):
    __tablename__ = "tla3bny_matches"

    id: Mapped[int] = mapped_column(primary_key=True)
    home_academy_id: Mapped[int] = mapped_column(
        sa.ForeignKey("tla3bny_users.id"), nullable=False
    )
    away_academy_id: Mapped[int] = mapped_column(
        sa.ForeignKey("tla3bny_users.id"), nullable=False
    )
    age_category_id: Mapped[int] = mapped_column(
        sa.ForeignKey("tla3bny_age_categories.id"), nullable=False
    )

    # Explicit nullable=True: a match may be scheduled before its date is set
    # (the feed orders with nullslast). The column name shadows the imported
    # `date` type in the annotation, so nullability is stated rather than inferred.
    date: Mapped[date | None] = mapped_column(sa.Date, nullable=True)
    time: Mapped[str | None] = mapped_column(sa.String(10))
    venue: Mapped[str | None] = mapped_column(sa.String(255))

    duration_minutes: Mapped[int] = mapped_column(sa.Integer, default=60)
    num_periods: Mapped[int] = mapped_column(sa.Integer, default=2)
    max_substitutions: Mapped[int] = mapped_column(sa.Integer, default=5)

    status: Mapped[str] = mapped_column(
        code_enum(*codes.TLA3BNY_MATCH_STATUS), nullable=False, default="scheduled"
    )
    home_score: Mapped[int | None] = mapped_column(sa.Integer)
    away_score: Mapped[int | None] = mapped_column(sa.Integer)

    home_academy: Mapped["Tla3bnyUser"] = relationship(
        foreign_keys=[home_academy_id]
    )
    away_academy: Mapped["Tla3bnyUser"] = relationship(
        foreign_keys=[away_academy_id]
    )
    age_category: Mapped["Tla3bnyAgeCategory"] = relationship()
    events: Mapped[list["Tla3bnyMatchEvent"]] = relationship(
        back_populates="match", cascade="all, delete-orphan"
    )
    lineups: Mapped[list["Tla3bnyLineup"]] = relationship(
        back_populates="match", cascade="all, delete-orphan"
    )

    def to_dict(self, include_events: bool = False) -> dict:
        data = {
            "id": self.id,
            "home_academy_id": self.home_academy_id,
            "away_academy_id": self.away_academy_id,
            "home_academy_name": self.home_academy.name if self.home_academy else None,
            "away_academy_name": self.away_academy.name if self.away_academy else None,
            "home_academy_logo": self.home_academy.logo_path
            if self.home_academy
            else None,
            "away_academy_logo": self.away_academy.logo_path
            if self.away_academy
            else None,
            "age_category_id": self.age_category_id,
            "age_category": self.age_category.label if self.age_category else None,
            "date": self.date.isoformat() if self.date else None,
            "time": self.time,
            "venue": self.venue,
            "duration_minutes": self.duration_minutes,
            "num_periods": self.num_periods,
            "max_substitutions": self.max_substitutions,
            "status": self.status,
            "home_score": self.home_score,
            "away_score": self.away_score,
        }
        if include_events:
            data["events"] = [
                e.to_dict()
                for e in sorted(
                    self.events,
                    key=lambda x: (x.minute if x.minute is not None else 999),
                )
            ]
        return data

    def __repr__(self) -> str:
        return f"<Tla3bnyMatch {self.id}>"


class Tla3bnyMatchEvent(TimestampMixin, db.Model):
    __tablename__ = "tla3bny_match_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    match_id: Mapped[int] = mapped_column(
        sa.ForeignKey("tla3bny_matches.id"), nullable=False
    )
    player_id: Mapped[int | None] = mapped_column(
        sa.ForeignKey("tla3bny_players.id")
    )
    team_academy_id: Mapped[int | None] = mapped_column(
        sa.ForeignKey("tla3bny_users.id")
    )

    event_type: Mapped[str] = mapped_column(
        code_enum(*codes.TLA3BNY_EVENT_TYPE), nullable=False
    )
    minute: Mapped[int | None] = mapped_column(sa.Integer)
    related_event_id: Mapped[int | None] = mapped_column(
        sa.ForeignKey("tla3bny_match_events.id")
    )

    match: Mapped["Tla3bnyMatch"] = relationship(back_populates="events")
    player: Mapped["Tla3bnyPlayer | None"] = relationship()

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "match_id": self.match_id,
            "player_id": self.player_id,
            "player_name": self.player.name if self.player else None,
            "jersey_number": self.player.jersey_number if self.player else None,
            "team_academy_id": self.team_academy_id,
            "event_type": self.event_type,
            "minute": self.minute,
            "related_event_id": self.related_event_id,
        }


class Tla3bnyLineup(TimestampMixin, db.Model):
    __tablename__ = "tla3bny_lineups"

    id: Mapped[int] = mapped_column(primary_key=True)
    match_id: Mapped[int] = mapped_column(
        sa.ForeignKey("tla3bny_matches.id"), nullable=False
    )
    academy_id: Mapped[int] = mapped_column(
        sa.ForeignKey("tla3bny_users.id"), nullable=False
    )
    formation: Mapped[str | None] = mapped_column(sa.String(20))

    match: Mapped["Tla3bnyMatch"] = relationship(back_populates="lineups")
    academy: Mapped["Tla3bnyUser"] = relationship()
    slots: Mapped[list["Tla3bnyLineupSlot"]] = relationship(
        back_populates="lineup", cascade="all, delete-orphan"
    )

    __table_args__ = (
        sa.UniqueConstraint(
            "match_id", "academy_id", name="uq_tla3bny_lineup_match_academy"
        ),
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "match_id": self.match_id,
            "academy_id": self.academy_id,
            "academy_name": self.academy.name if self.academy else None,
            "formation": self.formation,
            "slots": [s.to_dict() for s in self.slots],
        }


class Tla3bnyLineupSlot(TimestampMixin, db.Model):
    __tablename__ = "tla3bny_lineup_slots"

    id: Mapped[int] = mapped_column(primary_key=True)
    lineup_id: Mapped[int] = mapped_column(
        sa.ForeignKey("tla3bny_lineups.id"), nullable=False
    )
    position_slot: Mapped[str | None] = mapped_column(sa.String(20))
    player_id: Mapped[int | None] = mapped_column(
        sa.ForeignKey("tla3bny_players.id")
    )
    is_substitute: Mapped[bool] = mapped_column(
        sa.Boolean, nullable=False, default=False
    )

    lineup: Mapped["Tla3bnyLineup"] = relationship(back_populates="slots")
    player: Mapped["Tla3bnyPlayer | None"] = relationship()

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "lineup_id": self.lineup_id,
            "position_slot": self.position_slot,
            "player_id": self.player_id,
            "player_name": self.player.name if self.player else None,
            "jersey_number": self.player.jersey_number if self.player else None,
            "photo_path": self.player.photo_path if self.player else None,
            "is_substitute": self.is_substitute,
        }
