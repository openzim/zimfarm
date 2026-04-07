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

    # copy SSH keys from accounts to workers. For each SSH key associated with
    # an account, create a copy for each worker that belongs to that account
    connection = op.get_bind()
    connection.execute(
        sa.text(
            """
            INSERT INTO sshkey (id, name, fingerprint, type, key, added, worker_id)
            SELECT
                uuid_generate_v4() as id,
                s.name,
                s.fingerprint,
                s.type,
                s.key,
                s.added,
                w.id as worker_id
            FROM sshkey s
            INNER JOIN worker w ON s.account_id = w.account_id
            WHERE s.account_id IS NOT NULL
        """
        )
    )

    # Delete the old SSH keys that were associated with accounts
    connection.execute(
        sa.text(
            """
            DELETE FROM sshkey
            WHERE account_id IS NOT NULL AND worker_id IS NULL
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

    # copy SSH keys from workers to accounts. Group by account and deduplicate SSH keys
    connection = op.get_bind()
    connection.execute(
        sa.text(
            """
            INSERT INTO sshkey (id, name, fingerprint, type, key, added, account_id)
            SELECT DISTINCT ON (w.account_id, s.fingerprint)
                uuid_generate_v4() as id,
                s.name,
                s.fingerprint,
                s.type,
                s.key,
                s.added,
                w.account_id
            FROM sshkey s
            INNER JOIN worker w ON s.worker_id = w.id
            WHERE s.worker_id IS NOT NULL
        """
        )
    )

    # Delete the old SSH keys that were associated with workers
    connection.execute(
        sa.text(
            """
            DELETE FROM sshkey
            WHERE worker_id IS NOT NULL AND account_id IS NULL
        """
        )
    )

    op.alter_column("sshkey", "account_id", nullable=False)
    op.drop_column("sshkey", "worker_id")
    op.create_foreign_key(
        "fk_sshkey_account_id_account", "sshkey", "account", ["account_id"], ["id"]
    )
