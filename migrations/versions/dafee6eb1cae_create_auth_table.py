"""create auth_table

Revision ID: dafee6eb1cae
Revises: f2359984d1a5
Create Date: 2023-04-20 11:35:33.769930

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'dafee6eb1cae'
down_revision = 'f2359984d1a5'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('chat_auth',
    sa.Column('auth_id', sa.Integer(), nullable=False),
    sa.Column('user_idf', sa.String(length=32), nullable=False, comment='用户标识符'),
    sa.Column('began_at', sa.Integer(), nullable=False, comment='开始时间'),
    sa.Column('end_at', sa.Integer(), nullable=False, comment='结束时间'),
    sa.PrimaryKeyConstraint('auth_id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('chat_auth')
    # ### end Alembic commands ###
