"""move ssh keys from account to worker

Revision ID: fddc3fbad602
Revises: 3d5b282d74cf
Create Date: 2026-04-07 04:26:24.245579

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "fddc3fbad602"
down_revision = "3d5b282d74cf"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("sshkey", sa.Column("worker_id", sa.Uuid(), nullable=True))
    op.drop_constraint("fk_sshkey_account_id_account", "sshkey", type_="foreignkey")
    op.alter_column("sshkey", "account_id", nullable=True)

    # move SSH keys from accounts to workers
    connection = op.get_bind()
    connection.execute(
        sa.text(
            """
            UPDATE sshkey
            SET worker_id = worker.id
            FROM worker
            WHERE sshkey.account_id = worker.account_id
        """
        )
    )

    op.alter_column("sshkey", "worker_id", nullable=False)
    op.drop_column("sshkey", "account_id")
    op.create_foreign_key(
        op.f("fk_sshkey_worker_id_worker"), "sshkey", "worker", ["worker_id"], ["id"]
    )


def downgrade() -> None:
    op.add_column(
        "sshkey",
        sa.Column("account_id", sa.UUID(), autoincrement=False, nullable=True),
    )
    op.drop_constraint(op.f("fk_sshkey_worker_id_worker"), "sshkey", type_="foreignkey")
    op.alter_column("sshkey", "worker_id", nullable=True)

    # move SSH keys from workers to accounts
    connection = op.get_bind()
    connection.execute(
        sa.text(
            """
            UPDATE sshkey
            SET account_id = worker.account_id
            FROM worker
            WHERE sshkey.worker_id = worker.id
        """
        )
    )

    op.alter_column("sshkey", "account_id", nullable=False)
    op.drop_column("sshkey", "worker_id")
    op.create_foreign_key(
        "fk_sshkey_account_id_account", "sshkey", "account", ["account_id"], ["id"]
    )
