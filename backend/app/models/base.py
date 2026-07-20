from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from app.extensions import db


def code_enum(*values: str, length: int = 24) -> sa.Enum:
    """A VARCHAR + CHECK constraint rather than a native MySQL ENUM.

    Native enums require a table rebuild to add a value; these do not.
    """
    return sa.Enum(*values, native_enum=False, length=length, validate_strings=True)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime, nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        sa.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )


def localized(value_en: str | None, value_ar: str | None, lang: str) -> str | None:
    """Bilingual fallback: the requested language, else the other one."""
    if lang == "ar":
        return value_ar or value_en
    return value_en or value_ar


__all__ = ["db", "code_enum", "TimestampMixin", "localized"]
