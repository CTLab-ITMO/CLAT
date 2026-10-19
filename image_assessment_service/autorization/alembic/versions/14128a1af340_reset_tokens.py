"""reset tokens

Revision ID: 14128a1af340
Revises: cb78fd2c0467
Create Date: 2025-05-13 18:14:46.803033

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '14128a1af340'
down_revision: Union[str, None] = 'cb78fd2c0467'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # Create password_reset_tokens table
    op.create_table('password_reset_tokens',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('token', sa.String(length=255), nullable=False),
                    sa.Column('email', sa.String(length=255), nullable=False),
                    sa.Column('expires_at', sa.DateTime(), nullable=False),
                    sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
                    sa.Column('used_at', sa.DateTime(), nullable=True),
                    sa.PrimaryKeyConstraint('id'),
                    sa.UniqueConstraint('token')
                    )

    # Create indexes
    op.create_index(op.f('ix_password_reset_tokens_token'), 'password_reset_tokens', ['token'], unique=True)
    op.create_index(op.f('ix_password_reset_tokens_email'), 'password_reset_tokens', ['email'])
    op.create_index(op.f('ix_password_reset_tokens_id'), 'password_reset_tokens', ['id'])


def downgrade():
    # Drop indexes
    op.drop_index(op.f('ix_password_reset_tokens_id'), table_name='password_reset_tokens')
    op.drop_index(op.f('ix_password_reset_tokens_email'), table_name='password_reset_tokens')
    op.drop_index(op.f('ix_password_reset_tokens_token'), table_name='password_reset_tokens')

    # Drop table
    op.drop_table('password_reset_tokens')