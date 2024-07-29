"""campaign progress

Revision ID: e01b2f7bdea8
Revises: 
Create Date: 2024-07-26 22:39:55.235876

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e01b2f7bdea8'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('campaign', schema=None) as batch_op:
        batch_op.add_column(sa.Column('progress', sa.Integer(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('campaign', schema=None) as batch_op:
        batch_op.drop_column('progress')

    # ### end Alembic commands ###
