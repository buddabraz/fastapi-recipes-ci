"""Интеграционные проверки HTTP API на настоящей временной SQLite-базе."""

from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from main import create_app

PAYLOAD = {
    "title": "Омлет",
    "cooking_time": 10,
    "ingredients": ["2 яйца", "50 мл молока"],
    "description": "Взбейте и обжарьте.",
}


@pytest.fixture
def client(tmp_path: Path) -> Iterator[TestClient]:
    """Каждый тест получает отдельный файл и полный lifespan приложения."""
    with TestClient(
        create_app(f"sqlite+aiosqlite:///{tmp_path.as_posix()}/test.db")
    ) as test_client:
        yield test_client


def test_create_list_detail(client: TestClient) -> None:
    assert client.get("/recipes").json() == []
    response = client.post("/recipes", json=PAYLOAD)
    assert response.status_code == 201
    recipe = response.json()
    assert recipe == {**PAYLOAD, "id": 1, "views": 0}
    assert response.headers["Location"] == "http://testserver/recipes/1"
    expected = [{"id": 1, "title": "Омлет", "views": 0, "cooking_time": 10}]
    assert client.get("/recipes").json() == expected
    assert client.get("/recipes").json() == expected
    for views in (1, 2):
        detail = client.get("/recipes/1")
        assert detail.status_code == 200
        assert detail.json() == {**recipe, "views": views}
        assert detail.headers["Cache-Control"] == "no-store"
    assert client.get("/recipes").json()[0]["views"] == 2


def test_sorting(client: TestClient) -> None:
    for title, minutes in [
        ("Долгий", 60),
        ("Быстрый", 5),
        ("Популярный", 120),
        ("Ещё быстрый", 5),
    ]:
        assert (
            client.post(
                "/recipes", json={**PAYLOAD, "title": title, "cooking_time": minutes}
            ).status_code
            == 201
        )
    assert [r["id"] for r in client.get("/recipes").json()] == [2, 4, 1, 3]
    for recipe_id in (1, 2, 3, 3):
        assert client.get(f"/recipes/{recipe_id}").status_code == 200
    assert [r["id"] for r in client.get("/recipes").json()] == [3, 2, 1, 4]


def test_missing_recipe(client: TestClient) -> None:
    response = client.get("/recipes/999")
    assert response.status_code == 404
    assert response.json() == {"detail": "Рецепт не найден"}
    assert client.get("/recipes").json() == []


@pytest.mark.parametrize("recipe_id", ["0", "-1", "abc"])
def test_invalid_id(client: TestClient, recipe_id: str) -> None:
    assert client.get(f"/recipes/{recipe_id}").status_code == 422


@pytest.mark.parametrize(
    "changes",
    [
        {"title": "  "},
        {"title": "x" * 201},
        {"cooking_time": 0},
        {"cooking_time": -1},
        {"cooking_time": 1.5},
        {"cooking_time": True},
        {"cooking_time": "10"},
        {"ingredients": []},
        {"ingredients": ["  "]},
        {"ingredients": [12]},
        {"ingredients": "яйца"},
        {"description": "\n "},
        {"views": 100},
        {"id": 10},
    ],
)
def test_invalid_body(client: TestClient, changes: dict[str, object]) -> None:
    assert client.post("/recipes", json={**PAYLOAD, **changes}).status_code == 422
    assert client.get("/recipes").json() == []


def test_required_fields_and_json(client: TestClient) -> None:
    for field in PAYLOAD:
        body = {key: value for key, value in PAYLOAD.items() if key != field}
        assert client.post("/recipes", json=body).status_code == 422
    assert client.post("/recipes", content="{").status_code == 422
    assert client.get("/recipes").json() == []


def test_whitespace_and_duplicate_titles(client: TestClient) -> None:
    for _ in range(2):
        response = client.post(
            "/recipes",
            json={**PAYLOAD, "title": "  Омлет  ", "ingredients": [" яйцо "]},
        )
        assert response.status_code == 201
        assert response.json()["title"] == "Омлет"
        assert response.json()["ingredients"] == ["яйцо"]
    assert len(client.get("/recipes").json()) == 2


def test_concurrent_views(client: TestClient) -> None:
    client.post("/recipes", json=PAYLOAD)
    with ThreadPoolExecutor(max_workers=8) as pool:
        responses = list(pool.map(lambda _: client.get("/recipes/1"), range(24)))
    assert all(response.status_code == 200 for response in responses)
    assert sorted(response.json()["views"] for response in responses) == list(
        range(1, 25)
    )
    assert client.get("/recipes").json()[0]["views"] == 24


def test_persistence(tmp_path: Path) -> None:
    url = f"sqlite+aiosqlite:///{tmp_path.as_posix()}/persistent.db"
    with TestClient(create_app(url)) as first:
        first.post("/recipes", json=PAYLOAD)
        first.get("/recipes/1")
    with TestClient(create_app(url)) as second:
        assert second.get("/recipes").json()[0]["views"] == 1
        assert second.get("/recipes/1").json() == {**PAYLOAD, "id": 1, "views": 2}


def test_documentation(client: TestClient) -> None:
    for path in ("/docs", "/redoc", "/openapi.json"):
        assert client.get(path).status_code == 200
    schema = client.get("/openapi.json").json()
    assert set(schema["paths"]) == {"/recipes", "/recipes/{recipe_id}"}
    assert "201" in schema["paths"]["/recipes"]["post"]["responses"]
    assert "404" in schema["paths"]["/recipes/{recipe_id}"]["get"]["responses"]
    for name in ("RecipeCreate", "RecipeSummary", "RecipeDetail", "ErrorResponse"):
        assert schema["components"]["schemas"][name]["description"]
        assert all(
            field.get("description")
            for field in schema["components"]["schemas"][name]["properties"].values()
        )
