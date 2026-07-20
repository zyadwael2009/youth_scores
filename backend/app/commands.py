"""Flask CLI commands, e.g. seeding the first super admin.

    flask create-admin --username me --password "secret" --role superadmin --name "..."
"""

import click

from app.extensions import db
from app.models import AdminUser
from app.models import codes


def register_commands(app):
    @app.cli.command("create-admin")
    @click.option("--username", required=True)
    @click.option("--password", required=True)
    @click.option("--role", default="superadmin", type=click.Choice(codes.ADMIN_ROLE))
    @click.option("--name", default=None, help="Full name (optional)")
    def create_admin(username, password, role, name):
        """Create an admin, or reset the password/role of an existing one."""
        user = AdminUser.query.filter_by(username=username).first()
        if user:
            user.set_password(password)
            user.role = role
            user.is_active = True
            if name:
                user.full_name = name
            action = "updated"
        else:
            user = AdminUser(username=username, full_name=name, role=role)
            user.set_password(password)
            db.session.add(user)
            action = "created"
        db.session.commit()
        click.echo(f"{action} admin '{username}' with role '{role}'")
