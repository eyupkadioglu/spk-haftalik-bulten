"""add ortalama_maliyet and maliyet_fiyat

Revision ID: 28a3160e3a96
Revises:
Create Date: 2026-05-23 17:12:30.711091

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '28a3160e3a96'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('fatura_kalem', schema=None) as batch_op:
        batch_op.add_column(sa.Column('maliyet_fiyat', sa.Numeric(precision=18, scale=4), nullable=True))

    with op.batch_alter_table('stok', schema=None) as batch_op:
        batch_op.add_column(sa.Column('ortalama_maliyet', sa.Numeric(precision=18, scale=4), nullable=True))


def downgrade():
    with op.batch_alter_table('stok', schema=None) as batch_op:
        batch_op.drop_column('ortalama_maliyet')

    with op.batch_alter_table('fatura_kalem', schema=None) as batch_op:
        batch_op.drop_column('maliyet_fiyat')
