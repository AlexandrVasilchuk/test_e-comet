"""empty message

Revision ID: b79fa659b576
Revises: 
Create Date: 2024-02-10 01:47:24.375086

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b79fa659b576"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """CREATE TABLE repositories (id SERIAL PRIMARY KEY, repo VARCHAR, owner VARCHAR, position_cur INTEGER, position_prev INTEGER, stars INTEGER, watchers INTEGER, forks INTEGER, open_issues INTEGER, language VARCHAR)"""
    )


def downgrade() -> None:
    op.execute("DROP TABLE repositories")
