"""create phone no for user column

Revision ID: 2a0bb4dab663
Revises: 
Create Date: 2026-09-21 21:51:42.870345

"""
import email
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2a0bb4dab663'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("phone_number", sa.String))

def downgrade() -> None:
    op.drop_column("users", "phone_number")