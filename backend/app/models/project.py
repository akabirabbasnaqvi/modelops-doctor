from datetime import datetime

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Project(Base):
    """Represent an ML monitoring project or workspace."""

    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        unique=True,
        index=True,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    problem_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    target_column: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    positive_class: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    metric_priority: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="f1",
        server_default="f1",
    )

    owner: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    def __repr__(self) -> str:
        return (
            f"Project(id={self.id!r}, "
            f"name={self.name!r}, "
            f"problem_type={self.problem_type!r})"
        )
