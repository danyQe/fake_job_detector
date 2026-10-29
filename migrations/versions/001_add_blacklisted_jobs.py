"""add blacklisted jobs table

Revision ID: 001
Revises: 
Create Date: 2024-04-11 08:45:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create blacklisted_jobs table
    op.create_table(
        'blacklisted_jobs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('job_url', sa.String(), nullable=False),
        sa.Column('job_title', sa.String(), nullable=True),
        sa.Column('company_name', sa.String(), nullable=True),
        sa.Column('is_fake', sa.Boolean(), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('reasoning', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('report_count', sa.Integer(), server_default='1', nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('job_url')
    )
    op.create_index(op.f('ix_blacklisted_jobs_job_url'), 'blacklisted_jobs', ['job_url'], unique=True)


def downgrade() -> None:
    # Drop blacklisted_jobs table
    op.drop_index(op.f('ix_blacklisted_jobs_job_url'), table_name='blacklisted_jobs')
    op.drop_table('blacklisted_jobs') 