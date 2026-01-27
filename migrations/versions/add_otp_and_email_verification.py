"""Add OTP model and email_verified field to User

Revision ID: add_otp_email_verify
Revises: cf603c1fffef
Create Date: 2026-01-23

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime

# revision identifiers, used by Alembic
revision = 'add_otp_email_verify'
down_revision = 'd3ab180a738f'
branch_labels = None
depends_on = None


def upgrade():
    # Add email_verified column to users table
    op.add_column('users', sa.Column('email_verified', sa.Boolean(), nullable=True, server_default='false'), schema='public')

    # Create OTP table
    op.create_table('otps',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=120), nullable=False),
        sa.Column('otp_code', sa.String(length=6), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('is_used', sa.Boolean(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        schema='public'
    )
    op.create_index(op.f('ix_otps_email'), 'otps', ['email'], unique=False, schema='public')


def downgrade():
    # Drop OTP table
    op.drop_index(op.f('ix_otps_email'), table_name='otps', schema='public')
    op.drop_table('otps', schema='public')

    # Remove email_verified column from users table
    op.drop_column('users', 'email_verified', schema='public')
