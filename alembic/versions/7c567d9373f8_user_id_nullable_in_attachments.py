"""user_id nullable in attachments

Revision ID: 7c567d9373f8
Revises: 84b055820898
Create Date: 2025-03-20 16:24:58.086046

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7c567d9373f8'
down_revision: Union[str, None] = '84b055820898'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # user_id 컬럼을 nullable로 변경
    pass

def downgrade():
    # 롤백을 위한 코드
    pass

