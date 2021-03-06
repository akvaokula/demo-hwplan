"""empty message

Revision ID: 2273b58937b7
Revises: 9e482f65fbac
Create Date: 2022-05-03 16:58:57.387475

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "2273b58937b7"
down_revision = "9e482f65fbac"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column("activities", sa.Column("userId", sa.Integer(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("activities", "userId")
    # ### end Alembic commands ###
