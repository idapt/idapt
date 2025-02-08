"""Init db

Revision ID: 3650958c3e83
Revises: 
Create Date: 2025-02-02 14:39:23.943732

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3650958c3e83'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('folders',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('path', sa.String(), nullable=False),
    sa.Column('original_path', sa.String(), nullable=False),
    sa.Column('parent_id', sa.Integer(), nullable=True),
    sa.Column('uploaded_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
    sa.Column('accessed_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
    sa.ForeignKeyConstraint(['parent_id'], ['folders.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('original_path'),
    sa.UniqueConstraint('path')
    )
    op.create_table('files',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('path', sa.String(), nullable=False),
    sa.Column('original_path', sa.String(), nullable=False),
    sa.Column('mime_type', sa.String(), nullable=True),
    sa.Column('dek', sa.String(), nullable=False),
    sa.Column('size', sa.Integer(), nullable=True),
    sa.Column('status', sa.Enum('PENDING', 'QUEUED', 'PROCESSING', 'COMPLETED', 'ERROR', name='filestatus'), nullable=False),
    sa.Column('error_message', sa.String(), nullable=True),
    sa.Column('processed_stacks', sa.JSON(), nullable=True),
    sa.Column('stacks_to_process', sa.JSON(), nullable=True),
    sa.Column('processing_started_at', sa.DateTime(), nullable=True),
    sa.Column('file_created_at', sa.DateTime(), nullable=False),
    sa.Column('file_modified_at', sa.DateTime(), nullable=False),
    sa.Column('uploaded_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
    sa.Column('accessed_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
    sa.Column('ref_doc_ids', sa.JSON(), nullable=True),
    sa.Column('folder_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['folder_id'], ['folders.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('original_path'),
    sa.UniqueConstraint('path')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('files')
    op.drop_table('folders')
    # ### end Alembic commands ###
