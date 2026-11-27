"""Асинхронные SQL-операции с рецептами."""

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from models import Recipe
from schemas import RecipeCreate


async def list_recipes(session: AsyncSession) -> list[Recipe]:
    """Популярные первыми; при равенстве быстрее готовящиеся, затем ID."""
    result = await session.scalars(
        select(Recipe).order_by(Recipe.views.desc(), Recipe.cooking_time, Recipe.id)
    )
    return list(result.all())


async def create_recipe(session: AsyncSession, data: RecipeCreate) -> Recipe:
    """Сохранить рецепт с нулём просмотров."""
    recipe = Recipe(**data.model_dump())
    async with session.begin():
        session.add(recipe)
        await session.flush()
    return recipe


async def open_recipe(session: AsyncSession, recipe_id: int) -> Recipe | None:
    """Атомарно увеличить счётчик, вернуть карточку либо None."""
    async with session.begin():
        result = await session.execute(
            update(Recipe)
            .where(Recipe.id == recipe_id)
            .values(views=Recipe.views + 1)
            .returning(Recipe)
        )
        return result.scalar_one_or_none()
