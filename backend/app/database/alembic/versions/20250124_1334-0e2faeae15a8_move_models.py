"""move models

Revision ID: 0e2faeae15a8
Revises: 10d922351c74
Create Date: 2025-01-24 13:34:47.898718

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision: str = '0e2faeae15a8'
down_revision: Union[str, None] = '10d922351c74'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
