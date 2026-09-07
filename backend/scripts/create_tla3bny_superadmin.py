"""Create (or update) a tla3bny super-admin account.

Run against the TARGET database — e.g. locally with DATABASE_URL set to the Railway
MySQL public proxy URL, or `railway run python -m scripts.create_tla3bny_superadmin ...`.

Idempotent: if the username already exists it's promoted to an ACTIVE super_admin and
its password is reset; otherwise a new account is created. The password is passed on
the command line and hashed with bcrypt — it is never stored in this file or the repo.

    python -m scripts.create_tla3bny_superadmin <username> <password>
"""
from __future__ import annotations

import sys

from app import create_app
from app.extensions import db
from app.models import Tla3bnyUser


def create_or_update_superadmin(username: str, password: str) -> tuple[Tla3bnyUser, bool]:
    """Inside an app context: create or promote+reset a super_admin. Returns
    (user, created)."""
    login = Tla3bnyUser.normalize_login(username)
    if not login:
        raise ValueError("username is required")
    user = Tla3bnyUser.query.filter_by(username=login).first()
    created = user is None
    if user is None:
        user = Tla3bnyUser(username=login)
        db.session.add(user)
    user.role = "super_admin"
    user.status = "active"
    user.set_password(password)
    db.session.commit()
    return user, created


def main(username: str, password: str) -> None:
    # Enforce the same password policy the app does, so a live super-admin isn't weaker.
    from app.api.tla3bny._helpers import _validate_password
    err = _validate_password(password)
    if err:
        raise SystemExit(f"Password rejected by the policy: {err}")

    app = create_app()
    with app.app_context():
        user, created = create_or_update_superadmin(username, password)
        action = "Created" if created else "Updated existing account →"
        print(f"{action} tla3bny super_admin: username={user.username!r} "
              f"(id={user.id}), role=super_admin, status=active")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(
            "Usage: python -m scripts.create_tla3bny_superadmin <username> <password>")
    main(sys.argv[1], sys.argv[2])
