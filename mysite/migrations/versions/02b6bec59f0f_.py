"""empty message

Revision ID: 02b6bec59f0f
Revises: 399897c8f915
Create Date: 2018-03-17 16:27:52.289713

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = '02b6bec59f0f'
down_revision = '399897c8f915'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.rename_table('Profiles', 'profiles')
    op.rename_table('User_Records', 'user_records')
    op.rename_table('UserCache', 'usercache')
    op.rename_table('Users', 'users')
    op.rename_table('Cache_Records', 'cache_records')
    op.rename_table('UserActivity', 'useractivity')



def downgrade():
    op.rename_table('profiles', 'Profiles')
    op.rename_table('user_records', 'User_Records')
    op.rename_table('usercache', 'UserCache')
    op.rename_table('users', 'Users')
    op.rename_table('cache_records', 'Cache_Records')
    op.rename_table('useractivity', 'UserActivity')
