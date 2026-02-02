# Release Notes: v0.3.1

**Release date:** 2026-02-02

The v0.3.x series completes the project lifecycle and governance UI, making metaFirst usable for day-to-day lab operations without API access.

## Summary

v0.3.1 adds UI-driven project creation, RDMP management, supervisor member administration, and a projects overview page. Authorization is now fully supervisor-scoped, and the demo seed creates operational projects out of the box.

## Key Features

### Project Lifecycle UI

- **Create Project wizard**: Multi-step wizard to create projects with initial RDMP setup. Blocks ingest until RDMP is activated.
- **Project Settings page**: View and edit project configuration, manage storage roots.
- **RDMP Management page**: View RDMP versions, activate drafts (PI only), see lifecycle (DRAFT → ACTIVE → SUPERSEDED).

### Supervisor-Scoped Authorization

- **Project visibility**: Users only see projects belonging to supervisors they are members of.
- **Project access**: All project operations verify supervisor membership.
- **Member management UI**: PIs can add/remove supervisor members and change roles via `/supervisors/:id/members`.

### Sample ID Detection

- **Extraction rules**: Projects can define regex patterns with capture groups to extract sample IDs from file paths.
- **Detection panel**: Ingest UI shows detected sample ID and matching existing samples.

### Projects Overview

- **All Projects view**: Dashboard showing all accessible projects with RDMP status (Active/No Active RDMP).
- **Search and navigation**: Filter projects, quick access to member management.

### Operational Improvements

- **Samples pagination**: API returns `{items, total, limit, offset}` for large sample lists.
- **Eager loading**: Samples endpoint uses SQLAlchemy `joinedload` to avoid N+1 queries.
- **Database index**: Index on `sample_field_values.sample_id` for faster field value lookups.
- **Demo seed**: Projects are created with ACTIVE RDMPs, ready for immediate use.

## Behavioral Changes

- `GET /api/projects/` returns only projects for supervisors the user belongs to.
- `GET /api/projects/{id}/samples` returns paginated response instead of array.
- UI caches are scoped by `projectId` and invalidated after wizard completion.
- RDMP activation is scoped to the specific project (not global).

## API Changes

### New Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /api/supervisors/{id}/members` | List supervisor members |
| `POST /api/supervisors/{id}/members` | Add supervisor member |
| `PATCH /api/supervisors/{id}/members/{user_id}` | Update member role (PI only) |
| `DELETE /api/supervisors/{id}/members/{user_id}` | Remove member (PI only) |

### Modified Endpoints

| Endpoint | Change |
|----------|--------|
| `GET /api/projects/{id}/samples` | Returns `{items, total, limit, offset}` instead of array |
| `GET /api/projects/` | Filters by supervisor membership |

## Known Limitations

- Member management requires PI role; STEWARDs can view but not modify.
- No bulk sample operations yet.
- Discovery UI is still API-only.

## Upgrade Notes

- Database migrations are required: `alembic upgrade head`
- Frontend expects paginated samples response; update any direct API consumers.
- Existing demo data may need re-seeding for ACTIVE RDMPs: `./scripts/install_supervisor.sh --seed`

## Contributors

Development assisted by Claude Code.
