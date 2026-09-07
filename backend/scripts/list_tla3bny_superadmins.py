"""List tla3bny super-admin (and competition-admin) accounts — to confirm one exists.

Read-only. Run against the target database, e.g.
    railway run python -m scripts.list_tla3bny_superadmins
or locally with DATABASE_URL set to the prod MySQL public proxy URL. Prints role,
username, status, id and creation time — never any password material.
"""
from __future__ import annotations

from app import create_app
from app.models import Tla3bnyUser


def list_admins() -> list[Tla3bnyUser]:
    """Every super_admin / competition_admin account, ordered by role then username."""
    return (
        Tla3bnyUser.query
        .filter(Tla3bnyUser.role.in_(("super_admin", "competition_admin")))
        .order_by(Tla3bnyUser.role, Tla3bnyUser.username)
        .all()
    )


def main() -> None:
    app = create_app()
    with app.app_context():
        rows = list_admins()
        if not rows:
            print("No tla3bny super_admin / competition_admin accounts found.")
            return
        print(f"{'role':16} {'username':20} {'status':10} {'id':>4}  created")
        for u in rows:
            created = (u.created_at.isoformat(sep=' ', timespec='minutes')
                       if u.created_at else '—')
            print(f"{u.role:16} {(u.username or '—'):20} {u.status:10} {u.id:>4}  {created}")


if __name__ == "__main__":
    main()
