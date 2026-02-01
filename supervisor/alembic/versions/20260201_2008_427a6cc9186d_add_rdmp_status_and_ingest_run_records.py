"""add_rdmp_status_and_ingest_run_records

Revision ID: 427a6cc9186d
Revises: 3ee990ffd925
Create Date: 2026-02-01 20:08:40.657079

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '427a6cc9186d'
down_revision = '3ee990ffd925'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create ingest_run_records table
    op.create_table('ingest_run_records',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('ops_run_id', sa.Integer(), nullable=True),
        sa.Column('rdmp_version_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['rdmp_version_id'], ['rdmp_versions.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_ingest_run_record_project', 'ingest_run_records', ['project_id'], unique=False)
    op.create_index(op.f('ix_ingest_run_records_id'), 'ingest_run_records', ['id'], unique=False)

    # Add new columns to rdmp_versions using batch mode for SQLite
    with op.batch_alter_table('rdmp_versions') as batch_op:
        batch_op.add_column(sa.Column('status', sa.Enum('DRAFT', 'ACTIVE', 'SUPERSEDED', name='rdmpstatus'), nullable=True))
        batch_op.add_column(sa.Column('title', sa.String(255), nullable=True))
        batch_op.add_column(sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True))
        batch_op.add_column(sa.Column('approved_by', sa.Integer(), nullable=True))
        batch_op.create_foreign_key('fk_rdmp_approved_by', 'users', ['approved_by'], ['id'])
        batch_op.create_index('ix_project_rdmp_status', ['project_id', 'status'])

    # Set defaults for existing rows
    op.execute("UPDATE rdmp_versions SET status = 'ACTIVE' WHERE status IS NULL")
    op.execute("UPDATE rdmp_versions SET title = 'Imported RDMP' WHERE title IS NULL")


def downgrade() -> None:
    with op.batch_alter_table('rdmp_versions') as batch_op:
        batch_op.drop_index('ix_project_rdmp_status')
        batch_op.drop_constraint('fk_rdmp_approved_by', type_='foreignkey')
        batch_op.drop_column('approved_by')
        batch_op.drop_column('updated_at')
        batch_op.drop_column('title')
        batch_op.drop_column('status')

    op.drop_index(op.f('ix_ingest_run_records_id'), table_name='ingest_run_records')
    op.drop_index('ix_ingest_run_record_project', table_name='ingest_run_records')
    op.drop_table('ingest_run_records')
