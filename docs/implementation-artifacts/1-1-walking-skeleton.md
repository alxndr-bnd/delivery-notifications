---
baseline_commit: 865aee61c9425943172c341a664750733312486c
---

# Story 1.1: Вход магазина и кабинет доставок на проде (walking skeleton)

Status: review

<!-- Validation optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a владелец магазина,
I want войти в Javi и увидеть свой экран доставок,
so that у меня есть рабочее место для доставок, доступное в проде.

**Бизнес-суть (одно предложение):** магазин входит и видит свой (пустой) экран доставок на `javi.serbito.rs`.

## Acceptance Criteria

1. **Given** инициализированный greenfield Django 6 проект (uv) с зарегистрированными apps (accounts, deliveries, notifications, integrations, tracking, tasks, common) и моделью `Shop` (1:1 с пользователем), **when** проект запущен локально, **then** `manage.py check` и `pytest` проходят, `ruff` чист.
2. **Given** пользователь-магазин существует, **when** он входит по **email + паролю** под ролью «магазин», **then** он попадает на мобайл-first экран «Dostave» (Доставки), пока пустой, в светлой теме кабинета, с постоянной кнопкой **«＋ Nova dostava»**.
3. **Given** неавторизованный пользователь, **when** он открывает `/app/` (кабинет), **then** он редиректится на страницу входа.
4. **Given** два разных магазина, **when** каждый смотрит свой экран доставок, **then** он видит только свои доставки (изоляция по `Shop`); сейчас у обоих пусто (empty-state).
5. **Given** существующий живой лендинг Этапа 0, **when** задеплоена эта история, **then** маркетинговый лендинг **остаётся доступен** на `https://javi.serbito.rs/` (сбор заявок Formspree не сломан), а кабинет живёт под `/app/`.
6. **Given** тег `v*.*.*`, **when** срабатывает существующий CI/CD, **then** Django-образ (gunicorn+whitenoise) собирается и деплоится в Cloud Run (serbito, europe-west1), приложение поднимается, вход работает на проде с персистентной БД (Cloud SQL Postgres).

## Tasks / Subtasks

- [x] **Task 1: Greenfield-скелет проекта (удалить старый Django, сохранить лендинг)** (AC: #1)
  - [x] Удалён старый Django (`orders/`, `transport_site/`, `manage.py`, `db.sqlite3`, `venv/`, `nginx.conf`); сохранены `landing/`, `.github/`, `SETUP_CICD.md`, `scripts/`, `docs/`.
  - [x] `uv init` + зависимости (Django 6.0.5, gunicorn, psycopg[binary], whitenoise, django-environ; dev: pytest-django, ruff).
  - [x] `django-admin startproject config .`.
  - [x] `config/settings.py` env-driven (USE_TZ, TIME_ZONE Europe/Belgrade, LANGUAGE_CODE sr-latn, whitenoise, STATIC_ROOT, DATABASE_URL); `.env.example`.
  - [x] ruff + pytest-django конфиг в `pyproject.toml`; `.pre-commit-config.yaml` обновлён (ruff + django-check).
- [x] **Task 2: Скелет доменных apps** (AC: #1)
  - [x] apps accounts/deliveries/notifications/integrations/tracking/tasks/common зарегистрированы в INSTALLED_APPS.
  - [x] `common/` заготовки `phone.py`, `timewindow.py`, `logging.py` (TODO для Epic 2/3).
- [x] **Task 3: Модель пользователя и Shop + изоляция** (AC: #1, #4)
  - [x] Кастомный `accounts.User` (email-логин, без username) + `UserManager`; `AUTH_USER_MODEL`.
  - [x] `deliveries.Shop` (1:1 User): name + origin-заглушки; миграции.
  - [x] Скоуп по `request.user.shop` в `DeliveryListView`.
  - [x] management-команда `create_shop` (email/пароль/name) + Django admin.
- [x] **Task 4: Аутентификация (email+пароль)** (AC: #2, #3)
  - [x] `LoginView`/`LogoutView`, `LOGIN_URL`, `LOGIN_REDIRECT_URL=/app/`, `LOGOUT_REDIRECT_URL=/`.
  - [x] Экран входа — мобайл-first, светлая тема, бренд.
- [x] **Task 5: Экран кабинета «Dostave» (пустой) + лейаут** (AC: #2, #4)
  - [x] `DeliveryListView` (login_required) под `/app/`, empty-state «Nema dostava danas».
  - [x] Постоянная «＋ Nova dostava» (disabled-заглушка до 1.3).
  - [x] `templates/base.html` + `static/css/app.css` (токены DESIGN.md), sr-латиница.
- [x] **Task 6: Маршрутизация + сохранение лендинга** (AC: #5)
  - [x] `config/urls.py`: `/app/`, `/accounts/`, `/admin/`. Лендинг на `/` через WhiteNoise (`WHITENOISE_ROOT=landing`, `WHITENOISE_INDEX_FILE`).
  - [x] Проверено локально: `/`, `/privacy.html`, `/robots.txt`, `/sitemap.xml`, `/og.png` → 200; Formspree-форма на месте.
- [x] **Task 7: Контейнер и деплой** (AC: #6)
  - [x] `Dockerfile` (python:3.12-slim + uv + gunicorn + whitenoise + collectstatic + миграции на старте); `.dockerignore` обновлён; `deploy.yaml` — Cloud SQL + секреты + env.
  - [x] БД `javi` + пользователь `javi` на `serbitodb`; Secret Manager (`javi-secret-key`, `javi-database-url`); роли runtime-SA (cloudsql.client + secretAccessor на оба секрета).
  - [x] Деплой тегом `v0.3.0` (CI/CD зелёный); smoke-check прод: `/`→200 (лендинг+Formspree цел), `/app/`→302 на вход, `/accounts/login/`→200, `/privacy.html|/og.png|/robots.txt`→200. Миграции на проде прошли (страница входа рендерится).
  - [ ] _Завести демо-магазин на проде (`create_shop`) для проверки реального входа — прямой write в прод-БД, ждёт явного одобрения заказчика._
- [x] **Task 8: Тесты (pytest-django)** (AC: #1–#4)
  - [x] Аноним → `/app/` 302 на вход.
  - [x] Магазин видит пустой кабинет; изоляция по shop.
  - [x] Вход по email+паролю; `create_shop`.
  - [x] `manage.py check`, `pytest` (6 passed), `ruff check` — зелёные.

## Dev Notes

- **Greenfield, подтверждено заказчиком:** старый Django (`orders/`, `transport_site/`) удаляется. **Лендинг `landing/` критичен и живой** (Этап 0, собирает заявки Formspree) — не ломать; Django отдаёт его на `/`.
- **Стек (архитектура):** Python 3.12+, **Django 6.0** (актуальный стабильный, май 2026), uv, gunicorn, whitenoise, Cloud SQL Postgres, env-config (django-environ), Secret Manager. НЕ cookiecutter-django, НЕ Celery/Redis. [Source: docs/planning-artifacts/architecture.md#Starter Template Evaluation, #Core Architectural Decisions]
- **Apps и границы:** `config/` + accounts/deliveries/notifications/integrations/tracking/tasks/common; тонкие views + логика в `services.py`; провайдеры только через `integrations` (в 1.1 не задействованы). [Source: architecture.md#Project Structure & Boundaries]
- **Паттерны:** snake_case Python/БД; модели в ед.числе; UTC-хранение (`USE_TZ=True`), показ Europe/Belgrade; email-логин. [Source: architecture.md#Implementation Patterns]
- **UX:** мобайл-first светлая тема «Clean» (токены — DESIGN.md frontmatter); экран «Dostave» с группами и постоянной «＋ Nova dostava»; empty-state; строки sr-латиница. [Source: ux-designs/ux-Javi-2026-06-02/DESIGN.md, EXPERIENCE.md#Information Architecture, #State Patterns]
- **Деплой:** существующий CI/CD (`.github/workflows/deploy.yaml`, тег `v*.*.*` → Cloud Run `javi`, serbito/europe-west1). Меняем только Dockerfile + добавляем Cloud SQL/секреты. [Source: SETUP_CICD.md, architecture.md#Infrastructure & Deployment]
- **Изоляция арендаторов (NFR-6):** любой queryset доставок скоупится по `request.user.shop`.

### Project Structure Notes
- Целевое дерево — см. architecture.md#Complete Project Directory Structure. В 1.1 создаём скелет целиком, наполняем только accounts/deliveries. Delivery-модель и форма — в 1.3 (не здесь).
- Конфликт/вариация: в репо сейчас старый Django-проект + лендинг; 1.1 сносит старый проект, лендинг переносится под отдачу Django (`/`).

### References
- [Source: docs/planning-artifacts/epics.md#Story 1.1] — история, AC.
- [Source: docs/planning-artifacts/prds/prd-javi-2026-06-01/prd.md#4.1] — FR-1 (вход, изоляция).
- [Source: docs/planning-artifacts/architecture.md] — стек, apps, паттерны, деплой.
- [Source: docs/planning-artifacts/ux-designs/ux-Javi-2026-06-02/DESIGN.md, EXPERIENCE.md] — тема, IA, состояния, микрокопирайт.

### Решения заказчика (зафиксированы 2026-06-03)
1. **БД:** переиспользуем существующий Cloud SQL `serbitodb` (POSTGRES_17, europe-west1) — новая база `javi` + выделенный пользователь, доступ только к ней. Нулевая доп. стоимость, изоляция от serbito. _(Instance connection name: `serbito:europe-west1:serbitodb`.)_
2. **Лендинг + кабинет:** один сервис — Django отдаёт лендинг на `/`, кабинет под `/app/`. Лендинг Этапа 0 (Formspree) не ломать.
3. **Регистрация:** в 1.1 — management-команда `create_shop` (+ admin); полноценная регистрация — отдельная история позже.

## Dev Agent Record

### Agent Model Used

claude-opus-4-8 (1M context)

### Debug Log References

- manifest-storage статики ломала pytest без collectstatic → backend статики сделан переключаемым через env (`STATICFILES_BACKEND`), прод включает WhiteNoise manifest.
- `--set-env-vars` конфликтует с запятыми в ALLOWED_HOSTS → кастомный разделитель gcloud `^@@^`.

### Completion Notes List

- Реализован walking skeleton локально: greenfield Django 6.0.5, кастомный User (email), Shop, вход/выход, кабинет `/app/` (пустой, скоуп по магазину), команда `create_shop`.
- Лендинг Этапа 0 сохранён: отдаётся WhiteNoise на `/` (+ /privacy.html, /robots.txt, /sitemap.xml, /og.png), Formspree-форма цела. AC#5 ✅.
- Контейнер/деплой подготовлены (Dockerfile Django+gunicorn, .dockerignore, deploy.yaml с Cloud SQL+секретами). **AC#6 (прод-деплой) НЕ закрыт** — ждёт go: создание БД `javi`+пользователя на `serbitodb`, Secret Manager секретов, ролей runtime-SA, и тег-деплоя (трогает живой сервис).
- Проверки зелёные: `manage.py check`, `pytest` (6 passed), `ruff check`. AC#1–#4 ✅.
- Статус истории — `in-progress` (не `review`): Task 7 (прод) не завершён.

### File List

**Новые:**
- pyproject.toml, uv.lock, .env.example
- config/settings.py (перезапись), config/urls.py (перезапись)
- accounts/{models,admin,urls,tests}.py, accounts/migrations/0001_initial.py
- accounts/management/commands/create_shop.py (+ __init__.py)
- deliveries/{models,admin,views,urls,tests}.py, deliveries/migrations/0001_initial.py
- deliveries/templates/deliveries/delivery_list.html
- notifications/, integrations/, tracking/, tasks/, common/ (скелеты apps)
- common/{phone,timewindow,logging}.py (заглушки)
- templates/base.html, templates/accounts/login.html
- static/css/app.css

**Изменены:**
- Dockerfile (nginx → Django/gunicorn), .dockerignore, .gitignore
- .pre-commit-config.yaml (ruff + django-check)
- .github/workflows/deploy.yaml (Cloud SQL + секреты + env)

**Удалены (greenfield):**
- orders/, transport_site/, manage.py(старый)→пересоздан, db.sqlite3, nginx.conf, venv/, старые requirements*.txt/pyproject.toml
