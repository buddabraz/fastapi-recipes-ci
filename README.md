# Кулинарная книга — FastAPI и CI

Практическая 30.4: приложение из работы 26.4 перенесено в отдельный
репозиторий. Модели SQLAlchemy, SQL-операции и HTTP-контроллеры разделены.
SQLite и асинхронная сессия на каждый запрос; база создаётся при запуске.

## Запуск

Нужен Python 3.14.

```sh
python -m venv .venv
# Linux/macOS: source .venv/bin/activate
# Windows PowerShell: .venv/Scripts/Activate.ps1
python -m pip install -r requirements-dev.txt
python -m uvicorn main:app
```

Документация: http://127.0.0.1:8000/docs и /redoc, схема: /openapi.json.
DATABASE_URL задаёт альтернативную базу; по умолчанию recipes.sqlite3.

- POST /recipes — создать рецепт, 201 и Location карточки.
- GET /recipes — список, views DESC, cooking_time ASC, id ASC.
- GET /recipes/{recipe_id} — карточка и атомарное увеличение views.

Пример тела POST:

```json
{
  "title": "Омлет",
  "cooking_time": 10,
  "ingredients": ["2 яйца", "50 мл молока"],
  "description": "Взбейте и обжарьте."
}
```

## Проверки

```sh
python -m black --check .
python -m isort --check-only .
python -m flake8 .
python -m mypy
python -m pytest -q
```

GitHub Actions (.github/workflows/ci.yml) запускает эти пять проверок
отдельными заданиями на каждый push в любую ветку, каждый pull request
и вручную. Ошибка одной проверки не отменяет остальные; ошибка команды
делает задание неуспешным. Права workflow ограничены чтением содержимого.
Для запрета слияния при ошибках в настройках ветки следует потребовать
все пять статусов: black, isort, flake8, mypy, pytest.

Black и isort используют единый профиль. Flake8 использует длину 88
и исключает E203 для совместимости с Black. Mypy работает в strict-режиме
для всех пяти Python-файлов, включая тесты.

25 интеграционных тестов проверяют создание, чтение, сортировку,
валидацию, 404, сохранение после перезапуска, OpenAPI и 24 конкурентных
открытия карточки без потери просмотров. Каждый тест использует временную БД.

Настройка событий CI: [официальная документация GitHub Actions](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax).
