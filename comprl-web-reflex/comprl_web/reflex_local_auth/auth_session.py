import datetime

from comprl.server.data.models import Base

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column


class LocalAuthSession(
    Base,
):
    """Correlate a session_id with an arbitrary user_id."""

    __tablename__ = "auth_sessions"

    id: Mapped[int] = mapped_column(init=False, primary_key=True)
    user_id: Mapped[int] = mapped_column(index=True, nullable=False)
    session_id: Mapped[str] = mapped_column(
        sa.String(255), unique=True, index=True, nullable=False
    )
    expiration: Mapped[datetime.datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.sql.func.now(), nullable=False
    )
