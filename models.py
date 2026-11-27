"""Таблица рецептов кулинарной книги."""

from sqlalchemy import JSON, CheckConstraint, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Базовый класс декларативных моделей."""


class Recipe(Base):
    """Рецепт; ингредиенты хранятся упорядоченным JSON-списком строк."""

    __tablename__ = "recipes"
    __table_args__ = (
        CheckConstraint("cooking_time > 0"),
        CheckConstraint("views >= 0"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    cooking_time: Mapped[int] = mapped_column(Integer)
    ingredients: Mapped[list[str]] = mapped_column(JSON)
    description: Mapped[str] = mapped_column(Text)
    views: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
