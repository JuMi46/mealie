# Adding a DB table in Mealie

## Important locations

| Area | Link | Notes |
|---|---|---|
| Backend DB models | [models folder](../mealie/db/models/) | Add the SQLAlchemy/database model here |
| Backend schemas | [schema folder](../mealie/schema/) | Add request/response schemas here |
| Repositories | [repos folder](../mealie/repos/) | Add database access logic here |
| API routes | [routes folder](../mealie/routes/) | Add or update endpoints here |
| Alembic migrations | [migration folder](../alembic/versions/) | Add DB migration files here |

## Example files

- [Migration examples](../alembic/versions/)

### Group
- [User model](../mealie/db/models/users/users.py)
- [Recipe schema](../mealie/schema/recipe/recipe.py)

### Household

### User
- [User model](../mealie/db/models/users/users.py)
- [User schema](../mealie/schema/user/user.py)

### Recipe
