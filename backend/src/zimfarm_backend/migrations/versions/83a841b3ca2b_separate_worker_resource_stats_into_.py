"""separate worker resource stats into total and remaining

Revision ID: 83a841b3ca2b
Revises: e8556436e74a
Create Date: 2026-04-14 11:05:05.887945

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "83a841b3ca2b"
down_revision = "e8556436e74a"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add new columns as nullable first
    op.alter_column("worker", "cpu", new_column_name="total_cpu")
    op.alter_column("worker", "memory", new_column_name="total_memory")
    op.alter_column("worker", "disk", new_column_name="total_disk")
    op.add_column("worker", sa.Column("available_cpu", sa.Integer(), nullable=True))
    op.add_column(
        "worker", sa.Column("available_memory", sa.BigInteger(), nullable=True)
    )
    op.add_column("worker", sa.Column("available_disk", sa.BigInteger(), nullable=True))

    # Copy existing values to both total and remaining columns
    op.execute(
        """
        UPDATE worker
        SET available_cpu = total_cpu,
            available_memory = total_memory,
            available_disk = total_disk
        """
    )

    # Set new columns to non-nullable
    op.alter_column("worker", "available_cpu", nullable=False)
    op.alter_column("worker", "available_memory", nullable=False)
    op.alter_column("worker", "available_disk", nullable=False)


def downgrade() -> None:
    op.alter_column("worker", "total_cpu", new_column_name="cpu")
    op.alter_column("worker", "total_memory", new_column_name="memory")
    op.alter_column("worker", "total_disk", new_column_name="disk")
    op.drop_column("worker", "available_disk")
    op.drop_column("worker", "available_memory")
    op.drop_column("worker", "available_cpu")
