"""empty message

Revision ID: 3666fff4807e
Revises: b79fa659b576
Create Date: 2024-02-10 17:25:15.998951

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3666fff4807e'
down_revision: Union[str, None] = 'b79fa659b576'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        ALTER TABLE repositories
        ADD CONSTRAINT repo_unique UNIQUE (repo);
    """)


def downgrade() -> None:
    op.execute("""
    ALTER TABLE repositories
     DROP CONSTRAINT repo_unique
     """)
