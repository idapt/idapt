"""Add processing stacks

Revision ID: 1df0ba1d4e03
Revises: d998b6870e22
Create Date: 2025-01-14 09:52:41.064228

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1df0ba1d4e03'
down_revision: Union[str, None] = 'd998b6870e22'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('processing_stacks',
    sa.Column('identifier', sa.String(), nullable=False),
    sa.Column('display_name', sa.String(), nullable=False),
    sa.Column('description', sa.String(), nullable=True),
    sa.Column('is_enabled', sa.Boolean(), nullable=True),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('identifier')
    )
    op.create_table('processing_steps',
    sa.Column('identifier', sa.String(), nullable=False),
    sa.Column('display_name', sa.String(), nullable=False),
    sa.Column('description', sa.String(), nullable=True),
    sa.Column('type', sa.String(), nullable=False),
    sa.Column('parameters_schema', sa.JSON(), nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('identifier')
    )
    op.create_table('processing_stack_steps',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('stack_identifier', sa.String(), nullable=True),
    sa.Column('step_identifier', sa.String(), nullable=True),
    sa.Column('order', sa.Integer(), nullable=False),
    sa.Column('parameters', sa.JSON(), nullable=True),
    sa.ForeignKeyConstraint(['stack_identifier'], ['processing_stacks.identifier'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['step_identifier'], ['processing_steps.identifier'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('processing_stack_steps')
    op.drop_table('processing_steps')
    op.drop_table('processing_stacks')
    # ### end Alembic commands ###
