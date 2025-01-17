"""add file original path

Revision ID: 3083d9e553d3
Revises: ff2bd21827f5
Create Date: 2025-01-17 15:16:13.674056

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
# revision identifiers, used by Alembic.
revision: str = '3083d9e553d3'
down_revision: Union[str, None] = 'ff2bd21827f5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # For other databases, use regular operations
    op.add_column('files', sa.Column('original_path', sa.String(), nullable=False))
    op.create_unique_constraint('uq_files_original_path', 'files', ['original_path'])


def downgrade() -> None:
        op.drop_constraint('uq_files_original_path', 'files', type_='unique')
        op.drop_column('files', 'original_path')
