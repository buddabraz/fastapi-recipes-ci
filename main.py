"""Асинхронный HTTP API кулинарной книги. Запуск: uvicorn main:app."""

import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException
from fastapi import Path as ApiPath
from fastapi import Request, Response
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

import repositories
from models import Base
from schemas import ErrorResponse, RecipeCreate, RecipeDetail, RecipeSummary


async def get_session(request: Request) -> AsyncIterator[AsyncSession]:
    """Отдельная сессия на запрос, закрываемая также при исключении."""
    async with request.app.state.sessions() as session:
        yield session


Session = Annotated[AsyncSession, Depends(get_session)]


def create_app(database_url: str | None = None) -> FastAPI:
    """Создать приложение; URL можно передать явно или через DATABASE_URL."""
    default_path = Path(__file__).with_name("recipes.sqlite3").as_posix()
    url: str = database_url or os.environ.get(
        "DATABASE_URL", f"sqlite+aiosqlite:///{default_path}"
    )

    @asynccontextmanager
    async def lifespan(application: FastAPI) -> AsyncIterator[None]:
        """Создать таблицы при запуске и освободить соединения при остановке."""
        engine = create_async_engine(url)
        application.state.sessions = async_sessionmaker(engine, expire_on_commit=False)
        try:
            async with engine.begin() as connection:
                await connection.run_sync(Base.metadata.create_all)
            yield
        finally:
            await engine.dispose()

    application = FastAPI(
        title="Кулинарная книга",
        version="1.0.0",
        lifespan=lifespan,
        description=(
            "Асинхронный API рецептов. Создайте рецепт через POST /recipes. "
            "Список отсортирован по views DESC, cooking_time ASC, id ASC. "
            "Каждый успешный GET карточки увеличивает просмотры на один. "
            "Создание и получение списка просмотры не увеличивают. "
            "Доступ без авторизации; все тела запросов и ответов — JSON."
        ),
        openapi_tags=[
            {"name": "recipes", "description": "Создание, список и карточки рецептов"}
        ],
    )

    @application.get(
        "/recipes",
        response_model=list[RecipeSummary],
        tags=["recipes"],
        summary="Получить все рецепты",
        description=(
            "Возвращает массив (пустая база: []). "
            "Просмотры не меняются; пагинации нет."
        ),
    )
    async def recipes(session: Session) -> list[RecipeSummary]:
        """Список для первого экрана, в порядке популярности."""
        return [
            RecipeSummary.model_validate(row)
            for row in await repositories.list_recipes(session)
        ]

    @application.post(
        "/recipes",
        response_model=RecipeDetail,
        status_code=201,
        tags=["recipes"],
        summary="Создать рецепт",
        description="Возвращает сохранённый рецепт с views=0 и Location карточки. "
        "Повторный POST создаёт отдельную запись; названия могут повторяться.",
        responses={
            201: {
                "headers": {
                    "Location": {
                        "description": "URL карточки",
                        "schema": {"type": "string"},
                    }
                }
            }
        },
    )
    async def add_recipe(
        data: RecipeCreate, response: Response, request: Request, session: Session
    ) -> RecipeDetail:
        """Проверить поля и сохранить новый рецепт."""
        recipe = await repositories.create_recipe(session, data)
        response.headers["Location"] = str(
            request.url_for("recipe_detail", recipe_id=recipe.id)
        )
        return RecipeDetail.model_validate(recipe)

    @application.get(
        "/recipes/{recipe_id}",
        response_model=RecipeDetail,
        tags=["recipes"],
        summary="Открыть карточку рецепта",
        description=(
            "Увеличивает views на 1 атомарным SQL UPDATE. "
            "Ответ содержит обновлённый счётчик. "
            "Повторный запрос (в том числе повтор после сетевой ошибки) "
            "считается новым просмотром."
        ),
        responses={
            404: {"model": ErrorResponse, "description": "Рецепта с таким ID нет"}
        },
    )
    async def recipe_detail(
        recipe_id: Annotated[
            int, ApiPath(gt=0, description="Положительный ID рецепта")
        ],
        session: Session,
        response: Response,
    ) -> RecipeDetail:
        """Карточка для второго экрана; отсутствующий ID даёт 404."""
        recipe = await repositories.open_recipe(session, recipe_id)
        if recipe is None:
            raise HTTPException(status_code=404, detail="Рецепт не найден")
        response.headers["Cache-Control"] = "no-store"
        return RecipeDetail.model_validate(recipe)

    return application


app = create_app()
