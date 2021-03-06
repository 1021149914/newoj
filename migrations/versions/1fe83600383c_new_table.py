"""new table

Revision ID: 1fe83600383c
Revises: d5d931a3a687
Create Date: 2019-02-20 12:21:15.694385

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1fe83600383c'
down_revision = 'd5d931a3a687'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('contest', sa.Column('beg_time', sa.DateTime(), nullable=True))
    op.add_column('contest', sa.Column('end_time', sa.DateTime(), nullable=True))
    op.add_column('contest', sa.Column('limit', sa.String(length=1), nullable=True))
    op.add_column('inform', sa.Column('limit', sa.String(length=1), nullable=True))
    op.add_column('problem', sa.Column('limit', sa.String(length=1), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('problem', 'limit')
    op.drop_column('inform', 'limit')
    op.drop_column('contest', 'limit')
    op.drop_column('contest', 'end_time')
    op.drop_column('contest', 'beg_time')
    # ### end Alembic commands ###
