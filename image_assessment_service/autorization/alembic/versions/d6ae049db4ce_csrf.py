"""empty message

Revision ID: d6ae049db4ce
Revises: d3f5000baea1
Create Date: 2026-01-02 23:17:38.625682

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd6ae049db4ce'
down_revision: Union[str, None] = 'd3f5000baea1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.create_table('csrf_tokens',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('token', sa.String(length=128), nullable=False),
                    sa.Column('session_id', sa.String(length=64), nullable=False),
                    sa.Column('purpose', sa.String(length=50), nullable=False),
                    sa.Column('created_at', sa.DateTime(), nullable=False),
                    sa.Column('expires_at', sa.DateTime(), nullable=False),
                    sa.Column('used_at', sa.DateTime(), nullable=True),
                    sa.PrimaryKeyConstraint('id')
                    )

    op.create_index(op.f('ix_csrf_tokens_token'), 'csrf_tokens', ['token'], unique=True)
    op.create_index(op.f('ix_csrf_tokens_expires_at'), 'csrf_tokens', ['expires_at'])


def downgrade():
    op.drop_index(op.f('ix_csrf_tokens_expires_at'), table_name='csrf_tokens')
    op.drop_index(op.f('ix_csrf_tokens_token'), table_name='csrf_tokens')

    op.drop_table('csrf_tokens')
