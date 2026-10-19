"""email confirmation

Revision ID: a41e8b1bf311
Revises: 14128a1af340
Create Date: 2025-05-13 18:14:46.803033

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a41e8b1bf311'
down_revision: Union[str, None] = '14128a1af340'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.add_column('users',
                  sa.Column('email_confirmed_at', sa.DateTime(), nullable=True))
    op.add_column('users',
                  sa.Column('email_confirm_token', sa.String(length=255), nullable=True))


def downgrade():
    op.drop_column('users', 'email_confirmed_at')
    op.drop_column('users', 'email_confirm_token')
