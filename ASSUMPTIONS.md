# FDPAC Backend: Architecture & Design Assumptions

This document explains the architectural decisions, design patterns, and assumptions made in building the FDPAC backend.

---

## Architecture Overview

### Why Async/Async-First Design?

**Choice**: Full async architecture using FastAPI + SQLAlchemy AsyncSession + asyncpg

**Rationale**:
1. **Non-Blocking I/O**: All database operations are async. While a single request to PostgreSQL isn't faster, the application can handle **concurrent requests** without blocking. A synchronous Uvicorn server can process ~10 concurrent requests; async can handle 100+.

2. **Better Resource Utilization**: Instead of thread-per-request, async uses coroutines. This reduces memory overhead and thread switching costs.

3. **Scalability for Financial Dashboard**: In production, dashboards often aggregate data across many records. Async allows the app to serve multiple concurrent dashboard requests without one slow aggregation blocking others.

4. **Render Free-Tier Deployment**: Render provides limited resources. Async makes better use of CPU and memory, reducing the likelihood of hitting resource limits.

5. **Future-Ready**: Async integrates well with WebSockets (e.g., real-time dashboard updates) and other async services.

**Implementation Details**:
- `create_async_engine()`: Creates async PostgreSQL/SQLite engine
- `AsyncSession`: Async ORM context manager; replaces `SessionLocal`
- Query Pattern: `select(...).where(...) → await db.execute() → result.scalars()`
- Dependency Injection: `async def get_db()` yields `AsyncSessionLocal()` instance
- All service functions are `async def`, all routes are `async def`

### Driver Selection

**Database Drivers**:
- **asyncpg** (runtime): Native async Postgres driver; faster than psycopg2 + threading
- **psycopg2** (migrations): Alembic's engine_from_config works best with sync drivers; URL normalization handles the conversion

**Why Dual Drivers?**:
Alembic (migration tool) was designed for synchronous engines. Rather than fork Alembic or use a less-tested async migration runner, we switch drivers:
- Runtime: `postgresql+asyncpg://...` (fast, async)
- Migrations: `postgresql+psycopg2://...` (proven, stable)

The config layer handles URL conversion:
```python
@property
def async_database_url(self) -> str:
    return self.database_url.replace("+psycopg2", "+asyncpg")
```

---

## Role & Access Control Model

### Three-Role Hierarchy

**Defined Roles**:
1. **Viewer**: Read-only access to dashboards. Cannot create/modify records. Used for stakeholders.
2. **Analyst**: Can view and filter records; can access dashboards. Used for data analysts. Cannot modify records or manage users.
3. **Admin**: Full access. Can create/modify/delete records and users. Can change user roles.

**Assumption**: Roles are created by system on startup (see `seed_roles()` in main.py). Role membership cannot be self-assigned.

### Access Control Implementation

**Pattern**: FastAPI dependency injection with role guards
```python
@router.post("", dependencies=[Depends(require_roles("admin"))])
async def create_user(...):
    ...
```

**Flow**:
1. `require_roles("admin")` returns a dependency function
2. Dependency calls `get_current_user()` (validates JWT token)
3. Extracts user's role from database
4. Compares role name to allowed roles
5. Returns 403 Forbidden if role not in allowed list
6. Otherwise, user is authorized to proceed

**Assumption**: Token validation happens before role check. If token is invalid, request fails with 401 before role is checked.

### User Status Management

**Fields**:
- `is_active`: Boolean, default True
- Users with `is_active=False` cannot login

**Assumption**: Disabled users are blocked at login time, not at authorization time. An admin can disable a user mid-session, but the active session remains valid until token expires.

---

## Data Model Assumptions

### User Model

**Fields**:
- `id`: Primary key
- `name`: Display name
- `email`: Unique, used for login
- `password_hash`: Bcrypt hash (never plain text)
- `role_id`: Foreign key to Role
- `is_active`: Boolean (default True)
- `created_at`: Timestamp (server-side)

**Assumptions**:
- Users assigned **viewer** role by default on signup
- Admins must explicitly change user roles
- Users cannot change their own role
- Email is the unique identifier (case-sensitive on most databases)

### Financial Record Model

**Fields**:
- `id`: Primary key
- `amount`: Float (supports cents via database precision)
- `type`: Enum (income/expense)
- `category`: String (e.g., "salary", "groceries")
- `date`: Date (YYYY-MM-DD format)
- `notes`: Text, optional
- `created_by`: Foreign key to User
- `created_at`: Timestamp (server-side)
- `deleted_at`: Timestamp, nullable (soft delete marker)

**Assumptions**:
- Amount is always positive; sign is determined by type
- Records are created by admin only (current_user.id stored as created_by)
- Soft delete: Setting `deleted_at` marks record as deleted without removing data
- Querying records always filters `WHERE deleted_at IS NULL` unless explicitly querying deleted records
- Date is immutable once set (can be updated via PUT, but must be a valid date)

### Soft Delete Strategy

**Why Soft Delete?**:
- **Audit Trail**: Deleted records can be recovered or investigated
- **Referential Integrity**: If records were hard-deleted, any dependent data (reports, archives) would fail
- **Regulatory**: Financial data often must be retained for auditing

**Implementation**:
```python
# Delete
record.deleted_at = datetime.now(timezone.utc)
await db.commit()

# Query (auto-excludes deleted)
select(FinancialRecord).where(FinancialRecord.deleted_at.is_(None))
```

**Assumption**: Soft-deleted records are returned as 404 to API clients. Admins can recover via direct database access if needed.

---

## Authentication & Security

### JWT Token Strategy

**Token Structure**:
- Header: `{ "alg": "HS256", "typ": "JWT" }`
- Payload: `{ "user_id": <int>, "exp": <unix_timestamp> }`
- Signature: HS256 with SECRET_KEY

**Assumptions**:
- Token expiration is set to **30 minutes** (configurable via `ACCESS_TOKEN_EXPIRE_MINUTES`)
- Token is issued on login; client stores in local storage or session
- Token is sent in all requests via `Authorization: Bearer <token>` header
- No refresh token mechanism (user logs in again after expiration)
- Secret key must be at least 32 characters (enforced at config load)

**Why HS256 (not RS256)**:
- Simpler to deploy (no key management infrastructure needed)
- RSA/RS256 is more secure for distributed systems; our single backend can use HS256

### Password Security

**Hashing**: bcrypt with configurable cost factor (default 12)
```python
from passlib.context import CryptContext
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
```

**Assumptions**:
- Passwords are hashed before storage; plain text never stored or logged
- Passwords are minimum 8 characters (enforced by Pydantic schema)
- Password changes overwrite previous hash (no history kept)

### Rate Limiting

**Implementation**: In-memory asyncio.Lock per endpoint
```python
async def rate_limit() -> None:
    async with _rate_lock: await sleep(0.2)  # ~5 req/sec per endpoint
```

**Endpoints Protected**: `/auth/register`, `/auth/login`

**Assumptions**:
- Rate limit is **5 requests per minute** (200ms delay per request)
- Limit is per-instance (if running multiple instances, each has its own limit)
- Not suitable for production multi-instance (use Redis for shared rate limiting)
- Clients exceeding limit receive a 200 response but with significant delay (simple rate limiting)

---

## API Response Format

### Standard Response Envelope

All responses follow this format:
```json
{
  "success": true,
  "message": "Human-readable message",
  "data": {}
}
```

**Assumptions**:
- `success`: Boolean. True = request succeeded (2xx status code)
- `message`: String describing what happened or what failed
- `data`: Object/array with response payload, or null on error/delete

### Status Codes

| Code | Meaning | Use When |
|------|---------|----------|
| 200 | OK | GET, PUT, PATCH, DELETE succeeded |
| 201 | Created | POST created resource successfully |
| 400 | Bad Request | Invalid input, validation failed, resource already exists |
| 401 | Unauthorized | Missing/invalid token |
| 403 | Forbidden | User lacks required role |
| 404 | Not Found | Resource doesn't exist (includes soft-deleted) |
| 429 | Too Many Requests | Rate limit exceeded (if implemented) |
| 500 | Server Error | Database error, unhandled exception |
| 503 | Service Unavailable | Database connection down (health checks) |

**Assumption**: 404 is returned for soft-deleted records (client sees as "deleted").

---

## Dashboard Analytics Assumptions

### Aggregation Strategy

**Summary Endpoint** (`/dashboard/summary`):
- Sums all income and expense records (excluding deleted)
- Net balance = total_income - total_expense
- Runs in-database using SQLAlchemy `func.sum()`

**Category Breakdown**:
- Groups records by category
- Sums amount per category
- Returns sorted by category name

**Monthly Trends**:
- Fetches all non-deleted records
- Buckets by `strftime('%Y-%m', date)` in application
- Sums income and expense within each month bucket

**Recent Activity**:
- Returns 10 most recent records by created_at descending
- Excludes soft-deleted

**Assumptions**:
- Large datasets (100k+ records) may cause memory issues with trends aggregation (fetches all records into memory)
- For production, trends should use database-side date bucketing
- Dashboard always includes deleted=false in calculation (soft-deleted records never shown to users)

---

## Database & Migration Strategy

### Alembic Integration

**Why Alembic?**:
- Standard Python migration tool for SQLAlchemy
- Tracks schema versions in `alembic_version` table
- Supports both auto-generated and manual migrations

**Flow**:
1. Developer creates migration: `alembic revision --autogenerate -m "Add user_id column"`
2. Migration file created in `migrations/versions/`
3. On deployment, `alembic upgrade head` runs (in Docker or manually)
4. Schema updated to latest version

**Assumptions**:
- Migrations run in order by timestamp
- `alembic downgrade -1` can revert the last migration (caution: may lose data)
- No manual SQL edits to schema; all changes via Alembic

### Docker Deployment Strategy

**Dockerfile Entry Point**:
```dockerfile
CMD sh -c "alembic upgrade head && exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-10000}"
```

**Assumptions**:
- Render provides `DATABASE_URL` environment variable
- Migrations run on container startup (no manual shell access needed)
- If migration fails, app doesn't start (safer than starting with outdated schema)
- Multiple container instances running migrations in parallel: Alembic uses row-level locking on `alembic_version` table (safe for concurrent migrations)

---

## Configuration & Environment

### Environment Variables

Required:
- `DATABASE_URL`: PostgreSQL or SQLite connection string
- `SECRET_KEY`: JWT signing key (min 32 characters)

Optional:
- `ALGORITHM`: JWT algorithm (default: HS256)
- `ACCESS_TOKEN_EXPIRE_MINUTES`: Token TTL (default: 30)
- `CORS_ORIGINS`: Comma-separated allowed origins (default: "*")
- `LOG_LEVEL`: Logging level (default: INFO)

**Assumptions**:
- Missing required env vars cause app startup failure
- Database URL is never logged (security)
- SECRET_KEY is never logged
- Config validation happens at app startup

### Local Development vs. Production

**Development** (local machine):
- Use SQLite: `DATABASE_URL=sqlite:///./fdpac.db`
- CORS disabled: `CORS_ORIGINS=*`
- Hot reload: `uvicorn app.main:app --reload`

**Production** (Render):
- Use PostgreSQL: `DATABASE_URL=postgresql+asyncpg://...`
- CORS restricted: `CORS_ORIGINS=https://your-frontend.com`
- Single instance, no reload
- Docker container

**Assumption**: `.env` files are for local development only; Render uses secret environment variables.

---

## Testing Assumptions

### Test Database Strategy

**SQLite for Tests**:
```python
# conftest.py
DATABASE_URL = "sqlite:///./test.db"
engine = create_async_engine(DATABASE_URL, ...)
```

**Assumptions**:
- Tests run in isolation with fresh schema on each test
- `conftest.py` handles setup (create tables) and teardown (drop tables)
- Async fixtures use `asyncio.run()` wrapper for pytest compatibility
- Tests never touch production database

### Test Client

Uses FastAPI's async TestClient (httpx):
```python
from httpx import AsyncClient
async with AsyncClient(app=app, base_url="http://test") as client:
    response = await client.post("/api/v1/auth/login", ...)
```

**Assumptions**:
- Tests are integration tests (hit full app + database)
- Unit tests (service functions isolated) are minimal
- Test data is seeded via fixtures (see `conftest.py`)

---

## Health & Readiness Probes

### Why Health Endpoints?

**Liveness** (`/health/liveness`):
- Checks if app process is running
- Returns 200 immediately (no I/O)
- Used by container orchestrators to know if app crashed

**Readiness** (`/health/readiness`):
- Checks if app can handle traffic (database available)
- Used by load balancers to exclude unavailable instances from routing
- Returns 503 if database unreachable

### Render Deployment Integration

**Assumptions**:
- Render checks `/health/readiness` on startup (waits for green before routing traffic)
- If readiness returns 503, Render retries every 10 seconds for up to 5 minutes
- After 5 minutes of failed readiness, deployment fails
- Health endpoints also help diagnose startup issues in logs

---

## Performance & Scalability Considerations

### Connection Pooling

**asyncpg**:
```python
engine = create_async_engine(
    database_url,
    echo=False,
    pool_size=20,  # Default connections in pool
    max_overflow=10,  # Extra connections if needed
)
```

**Assumptions**:
- Pool size of 20 is suitable for typical traffic
- Render free tier has connection limits (often 20-50); adjust if hitting limits
- Connection timeouts will cause 500 errors (see exception handlers in main.py)

### Query Optimization

**Eager Loading** (using `selectinload`):
```python
select(User).options(selectinload(User.role)).where(...)
```
Prevents N+1 query problem (fetching user role separately for each user).

**Filtering at Database** (not application):
```python
select(Record).where(Record.category == "salary")  # Fast
```
vs.
```python
all_records = [r for r in records if r.category == "salary"]  # Slow
```

**Assumptions**:
- Indexes created on foreign keys and frequently queried fields
- Large date ranges or high-frequency queries should use pagination
- Category breakdown with 100k records + 50 categories runs in <100ms on typical Postgres

---

## Future Enhancements (Out of Scope)

These are **not implemented** but documented for clarity:

1. **Refresh Tokens**: Extend session without re-login
2. **Multi-Factor Authentication**: Phone/email verification
3. **API Keys**: Third-party integrations
4. **Webhooks**: Notify external services on record create/update
5. **Real-Time Updates**: WebSocket endpoints for live dashboard
6. **Advanced Filtering**: Complex boolean expressions (category IN (...) AND date >= ...)
7. **Audit Logs**: Track who modified what record and when
8. **Redis Cache**: Cache dashboard aggregations (expensive queries)
9. **User Preferences**: Dark mode, default filters, layout memory
10. **File Uploads**: Attach receipts/invoices to records

---

## Summary of Key Decisions

| Decision | Choice | Why |
|----------|--------|-----|
| Framework | FastAPI | Fast, async-native, auto-docs |
| ORM | SQLAlchemy 2.0 + async | Type-safe, async support, migrations |
| Database | PostgreSQL (prod) / SQLite (tests) | ACID compliance, scalable |
| Auth | JWT with HS256 | Stateless, simple, no session DB needed |
| Role Model | 3 roles (viewer/analyst/admin) | Clear permissions, easy to understand |
| Delete Strategy | Soft delete | Audit trail, recovery, referential integrity |
| Rate Limiting | In-memory asyncio.Lock | Simple, but not suitable for multi-instance |
| Deployment | Docker on Render | Containerized, easy scaling, free tier viable |

---

**For questions or clarifications on architecture, refer to the code or raise an issue in the repository.**


### Universal Records Data Scope
**Assumption:** The application tracks finances for a singular corporate entity, rather than distinct personal accounts. The created_by field dictates authorship, not restrictive visibility. All records are un-siloed explicitly so roles fetch accurate, platform-wide aggregations.