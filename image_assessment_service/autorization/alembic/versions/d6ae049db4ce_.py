"""empty message

Revision ID: d6ae049db4ce
Revises: 0fd00338412a
Create Date: 2025-04-24 23:17:38.625682

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd6ae049db4ce'
down_revision: Union[str, None] = '0fd00338412a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
