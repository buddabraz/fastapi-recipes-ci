"""Входные и выходные модели OpenAPI."""

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

Ingredient = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=300)
]


class RecipeCreate(BaseModel):
    """Данные нового рецепта. ID и просмотры назначает сервер."""

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        json_schema_extra={
            "example": {
                "title": "Омлет",
                "cooking_time": 10,
                "ingredients": ["2 яйца", "50 мл молока", "соль по вкусу"],
                "description": "Взбейте яйца с молоком. Готовьте на сковороде 5 минут.",
            }
        },
    )

    title: str = Field(min_length=1, max_length=200, description="Название блюда")
    cooking_time: int = Field(
        gt=0, strict=True, description="Время приготовления в целых минутах"
    )
    ingredients: list[Ingredient] = Field(
        min_length=1, description="Ингредиенты с количеством, в порядке ввода"
    )
    description: str = Field(
        min_length=1, description="Текстовая инструкция приготовления"
    )


class RecipeSummary(BaseModel):
    """Строка таблицы рецептов, включая ID для открытия карточки."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(gt=0, description="Уникальный ID рецепта")
    title: str = Field(description="Название блюда")
    views: int = Field(ge=0, description="Количество успешных открытий карточки")
    cooking_time: int = Field(gt=0, description="Время приготовления в минутах")


class RecipeDetail(RecipeSummary):
    """Полная карточка; views включает текущее открытие через GET."""

    ingredients: list[str] = Field(description="Список ингредиентов с количеством")
    description: str = Field(description="Текстовая инструкция приготовления")


class ErrorResponse(BaseModel):
    """Ошибка обращения к отсутствующему рецепту."""

    detail: str = Field(description="Описание ошибки", examples=["Рецепт не найден"])
