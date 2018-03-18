"""empty message

Revision ID: bb74dc14138c
Revises: 71076ddf8ccc
Create Date: 2018-01-30 04:35:08.621300

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = 'bb74dc14138c'
down_revision = '71076ddf8ccc'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('UserCache', sa.Column('active', sa.Boolean(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('UserCache', 'active')
    # ### end Alembic commands ###
