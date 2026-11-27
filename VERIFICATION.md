# Проверка практической 30.4

27 ноября 2026 года, Windows, Python 3.14.0; отдельное виртуальное окружение.

- Black 26.10.1: 5 файлов без изменений (--check).
- isort 9.0.2: импорты корректны (--check-only).
- Flake8 7.5.0: ошибок нет.
- mypy 2.4.1: strict, ошибок нет во всех 5 Python-файлах.
- pytest 9.2.0: 25 passed за 1.68 с.

Есть предупреждение Starlette о будущем переходе TestClient на httpx2;
текущие тесты с зафиксированным httpx проходят. Предупреждение не подавлено.
Black и тесты зависли в ограниченной песочнице Windows; успешные результаты
получены повторным запуском с разрешённым доступом вне песочницы.

Workflow содержит отдельные задания black/isort/flake8/mypy/pytest;
события push и pull_request без фильтра веток, также workflow_dispatch.

GitHub Actions на Ubuntu / Python 3.14: все пять заданий прошли
и для push, и для pull_request (коммит 649f051).

- Push: https://github.com/buddabraz/fastapi-recipes-ci/actions/runs/45992045543
- PR: https://github.com/buddabraz/fastapi-recipes-ci/actions/runs/45992045977

Для main включена защита: PR перед слиянием, актуальность ветки, обязательные
black/isort/flake8/mypy/pytest от GitHub Actions; обход администратором запрещён.
Одобрение другого участника не требуется для индивидуального учебного проекта.
