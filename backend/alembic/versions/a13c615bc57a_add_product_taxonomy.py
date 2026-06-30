"""add_product_taxonomy

Revision ID: a13c615bc57a
Revises: 53899b7f161c
Create Date: 2026-05-08 21:25:43.243419

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a13c615bc57a'
down_revision: Union[str, Sequence[str], None] = '53899b7f161c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'product_taxonomy',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('product', sa.String(), nullable=False),
        sa.Column('platform', sa.Text(), nullable=True),
        sa.Column('sub_product', sa.Text(), nullable=True),
        sa.Column('solution', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('product'),
    )
    op.create_index('ix_product_taxonomy_id', 'product_taxonomy', ['id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_product_taxonomy_id', table_name='product_taxonomy')
    op.drop_table('product_taxonomy')
