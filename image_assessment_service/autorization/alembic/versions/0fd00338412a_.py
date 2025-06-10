"""empty message

Revision ID: 0fd00338412a
Revises: d3f5000baea1
Create Date: 2025-04-24 23:17:34.419790

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0fd00338412a'
down_revision: Union[str, None] = 'd3f5000baea1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
