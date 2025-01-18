"""add file and folder original path

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
    # Handle files table
    with op.batch_alter_table('files') as batch_op:
        batch_op.add_column(sa.Column('original_path', sa.String(), nullable=False))
        batch_op.create_unique_constraint('uq_files_original_path', ['original_path'])

    # Handle folders table
    with op.batch_alter_table('folders') as batch_op:
        batch_op.add_column(sa.Column('original_path', sa.String(), nullable=False))
        batch_op.create_unique_constraint('uq_folders_original_path', ['original_path'])


def downgrade() -> None:
    # Handle files table
    with op.batch_alter_table('files') as batch_op:
        batch_op.drop_constraint('uq_files_original_path', type_='unique')
        batch_op.drop_column('original_path')

    # Handle folders table
    with op.batch_alter_table('folders') as batch_op:
        batch_op.drop_constraint('uq_folders_original_path', type_='unique')
        batch_op.drop_column('original_path')
