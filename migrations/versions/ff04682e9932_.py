"""empty message

Revision ID: ff04682e9932
Revises: 6dbe242c2728
Create Date: 2018-02-02 23:03:54.093073

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ff04682e9932'
down_revision = '6dbe242c2728'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('UserActivity',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('active', sa.Boolean(), nullable=True),
    sa.Column('created', sa.DateTime(), nullable=True),
    sa.Column('new_records', sa.Integer(), nullable=True),
    sa.Column('borrowed_records', sa.Integer(), nullable=True),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['Users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('UserActivity')
    # ### end Alembic commands ###
