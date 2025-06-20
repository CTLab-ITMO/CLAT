"""annotation-task_id-index

Revision ID: 9aef398b6563
Revises: 8c5257af99f6
Create Date: 2025-04-26 03:41:43.156586

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9aef398b6563'
down_revision: Union[str, None] = '8c5257af99f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_index(op.f('ix_annotations_task_id'), 'annotations', ['task_id'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_annotations_task_id'), table_name='annotations')
    # ### end Alembic commands ###
