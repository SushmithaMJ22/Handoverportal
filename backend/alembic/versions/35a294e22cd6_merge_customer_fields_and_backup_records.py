"""merge customer_fields and backup_records

Revision ID: 35a294e22cd6
Revises: 5453b5aded5a, b1c2d3e4f5g6
Create Date: 2026-07-04 14:10:37.904152

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '35a294e22cd6'
down_revision: Union[str, Sequence[str], None] = ('5453b5aded5a', 'b1c2d3e4f5g6')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
