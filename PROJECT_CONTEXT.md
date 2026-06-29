# Project Context: Mealie

## Overview

This repository is Mealie, a self-hosted recipe management application.

The project is a full-stack application with:

- Python/FastAPI backend in `mealie/`
- Nuxt/Vue frontend in `frontend/app/`
- SQLAlchemy/database models and Alembic migrations
- Recipe management, recipe parsing/scraping/importing, meal planning, shopping lists, users, groups, households, authentication, backups, email, and admin functionality
- Backend tests in `tests/`

Use this file as the project map for Continue. Prefer targeted searches over broad full-codebase scans.

---

## High-Level Repo Map

### Backend

- `mealie/` — Main backend Python package.
- `mealie/routes/` — FastAPI route modules/endpoints.
- `mealie/services/` — Business logic and feature services.
- `mealie/repos/` — Repository/query/data-access layer.
- `mealie/schema/` — Pydantic schemas, request/response models, domain schemas.
- `mealie/db/` — Database setup, DB fixes, SQLAlchemy models.
- `mealie/alembic/versions/` — Database migrations.
- `mealie/core/` — App core, dependencies, logger, security, settings.
- `mealie/middleware/` — Backend middleware.
- `mealie/pkgs/` — Shared backend packages/utilities.
- `mealie/assets/` — Backend assets/static user-related assets.
- `mealie/lang/` — Backend localization/messages.
- `mealie/scripts/` — Backend scripts.

### Frontend

- `frontend/app/` — Main Nuxt/Vue frontend app.
- `frontend/app/pages/` — Page-level routes/views.
- `frontend/app/components/` — Reusable Vue components.
- `frontend/app/composables/` — Shared composables/hooks.
- `frontend/app/stores/` — Frontend stores if present.
- `frontend/app/types/` — Frontend TypeScript types.
- `frontend/app/lib/` — Frontend library/helper code.
- `frontend/app/middleware/` — Nuxt/frontend middleware.
- `frontend/app/lang/` — Frontend translations/localization.
- `frontend/server/` — Nuxt server-side routes/API if relevant.
- `frontend/public/` — Public static assets.

### Tests

- `tests/unit_tests/` — Unit tests.
- `tests/integration_tests/` — Integration tests.
- `tests/e2e/` — End-to-end tests.
- `tests/fixtures/` — Test fixtures.
- `tests/data/` — Test data.
- `tests/utils/` — Test utilities/helpers.

### Development, Docs, Docker

- `docs/` — Documentation.
- `docker/` — Docker-related files.
- `dev/scripts/` — Development scripts.
- `dev/code-generation/` — Code generation tools/templates.
- `dev/code-generation/generated/` — Generated code; usually ignore unless working on codegen.
- `.devcontainer/` — Dev container config.
- `.vscode/` — VS Code workspace config.

### Runtime/Generated Data

These are usually runtime/generated/local data and should not be searched unless specifically relevant:

- `data/`
- `dev/data/`
- `.pytest_cache/`
- `.ruff_cache/`
- `.task/`
- `frontend/.nuxt/`
- `mealie.egg-info/`
- `__pycache__/`

---

## Backend Feature Map

### Authentication and Security

Search first:

- `mealie/core/dependencies/`
- `mealie/schema/user/`
- `mealie/services/user_services/`
- `mealie/repos/`
- `frontend/app/pages/`
- `frontend/app/components/`
- `frontend/app/composables/`
- `frontend/app/middleware/`

Useful terms:

- `auth`
- `login`
- `token`
- `jwt`
- `session`
- `password`
- `permission`
- `current_user`
- `security`

---

### Users, Groups, and Households

Search first:

- `mealie/routes/users/`
- `mealie/routes/groups/`
- `mealie/routes/households/`
- `mealie/services/user_services/`
- `mealie/services/group_services/`
- `mealie/services/household_services/`
- `mealie/schema/user/`
- `mealie/schema/group/`
- `mealie/schema/household/`
- `mealie/db/models/`
- `frontend/app/pages/`
- `frontend/app/components/`

Useful terms:

- `user`
- `group`
- `household`
- `member`
- `admin`
- `permission`
- `invite`

---

### Recipes

Search first:

- `mealie/routes/recipe/`
- `mealie/services/recipe/`
- `mealie/schema/recipe/`
- `mealie/repos/`
- `mealie/db/models/`
- `frontend/app/pages/`
- `frontend/app/components/`
- `frontend/app/composables/`
- `frontend/app/types/`

Useful terms:

- `recipe`
- `slug`
- `ingredient`
- `instruction`
- `nutrition`
- `asset`
- `image`
- `yield`
- `serving`
- `recipe_id`

---

### Recipe Parsing, Scraping, and Importing

Search first:

- `mealie/routes/parser/`
- `mealie/services/parser_services/`
- `mealie/services/scraper/`
- `mealie/services/recipe/`
- `mealie/pkgs/`
- `mealie/schema/recipe/`
- `frontend/app/pages/`
- `frontend/app/components/`
- `frontend/app/composables/`

Useful terms:

- `parser`
- `parse`
- `scrape`
- `scraper`
- `import`
- `url`
- `html`
- `recipe-scrapers`
- `ingredient_parser`
- `bulk`

Relevant tests may be in:

- `tests/unit_tests/ingredient_parser/`
- `tests/unit_tests/services_tests/`
- `tests/integration_tests/user_recipe_tests/`
- `tests/data/html/`
- `tests/data/json/`

---

### Meal Planning

Search first:

- `mealie/routes/households/`
- `mealie/schema/meal_plan/`
- `mealie/services/household_services/`
- `mealie/repos/`
- `mealie/db/models/`
- `frontend/app/pages/`
- `frontend/app/components/`
- `frontend/app/composables/`

Useful terms:

- `meal_plan`
- `mealplan`
- `planner`
- `plan`
- `scheduled`
- `date`
- `random`

---

### Shopping Lists

Search first:

- `mealie/routes/households/`
- `mealie/services/household_services/`
- `mealie/schema/household/`
- `mealie/repos/`
- `mealie/db/models/`
- `frontend/app/pages/`
- `frontend/app/components/`
- `frontend/app/composables/`

Useful terms:

- `shopping`
- `shopping_list`
- `list_item`
- `food`
- `ingredient`
- `unit`
- `quantity`

---

### Foods, Units, Organizers, Labels, Categories, Tags, Tools

Search first:

- `mealie/routes/unit_and_foods/`
- `mealie/routes/organizers/`
- `mealie/schema/labels/`
- `mealie/schema/recipe/`
- `mealie/repos/`
- `mealie/db/models/`
- `frontend/app/pages/`
- `frontend/app/components/`

Useful terms:

- `food`
- `unit`
- `organizer`
- `label`
- `category`
- `tag`
- `tool`

Relevant tests may be in:

- `tests/integration_tests/category_tag_tool_tests/`
- `tests/unit_tests/repository_tests/`
- `tests/unit_tests/schema_tests/`

---

### Comments, Timers, Shared Recipes,
