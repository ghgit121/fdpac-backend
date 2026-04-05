# FDPAC Backend API Reference

Complete API endpoint documentation for the Financial Document Processing and Access Control (FDPAC) backend.

**Base URL**: `http://localhost:8000/api/v1` (development) or your Render deployment URL

**Authentication**: JWT Bearer token in `Authorization` header: `Authorization: Bearer <token>`

**Response Format**: All endpoints return:
```json
{
  "success": true,
  "message": "Operation description",
  "data": {}
}
```

Error responses:
```json
{
  "success": false,
  "message": "Error description",
  "errors": []
}
```

---

## Base Endpoints

### Root URL
- **Endpoint**: `GET /`
- **Authentication**: Not required
- **Description**: Verifies backend root resolution.
- **Response** (200 OK):
  ```json
  {
    "success": true,
    "message": "Welcome to FDPAC Backend API"
  }
  ```

## Authentication Endpoints

### Register User
- **Endpoint**: `POST /api/v1/auth/register`
- **Authentication**: Not required
- **Rate Limit**: 5 requests/minute
- **Role Required**: None
- **Request Body**:
  ```json
  {
    "name": "John Doe",
    "email": "john@example.com",
    "password": "securepassword123"
  }
  ```
- **Validation**:
  - `name`: 2-120 characters
  - `email`: Valid email format
  - `password`: Minimum 8 characters
- **Response** (201 Created):
  ```json
  {
    "success": true,
    "message": "User registered successfully",
    "data": {
      "id": 1,
      "name": "John Doe",
      "email": "john@example.com",
      "role": "viewer",
      "is_active": true
    }
  }
  ```
- **Error Cases**:
  - `400 Bad Request`: Email already exists, invalid email format, password too short
  - `500 Internal Server Error`: Default role missing (system configuration error)

### Login User
- **Endpoint**: `POST /api/v1/auth/login`
- **Authentication**: Not required
- **Rate Limit**: 5 requests/minute
- **Role Required**: None
- **Request Body**:
  ```json
  {
    "email": "john@example.com",
    "password": "securepassword123"
  }
  ```
- **Validation**:
  - `email`: Valid email format
  - `password`: Minimum 8 characters
- **Response** (200 OK):
  ```json
  {
    "success": true,
    "message": "Login successful",
    "data": {
      "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
      "token_type": "bearer",
      "expires_in_minutes": 30
    }
  }
  ```
- **Error Cases**:
  - `401 Unauthorized`: Invalid email/password combination
  - `403 Forbidden`: User account is disabled (is_active=false)
  - `400 Bad Request`: Invalid input format

### Get Current User
- **Endpoint**: `GET /api/v1/auth/me`
- **Authentication**: Required (JWT Bearer token)
- **Role Required**: None (all authenticated users)
- **Request**: No body
- **Response** (200 OK):
  ```json
  {
    "success": true,
    "message": "User info fetched successfully",
    "data": {
      "id": 1,
      "name": "John Doe",
      "email": "john@example.com",
      "role": "viewer",
      "is_active": true
    }
  }
  ```
- **Error Cases**:
  - `401 Unauthorized`: Missing or invalid token
  - `404 Not Found`: User not found (token points to deleted user)

---

## User Management Endpoints

### Create User
- **Endpoint**: `POST /api/v1/users`
- **Authentication**: Required
- **Role Required**: `admin`
- **Request Body**:
  ```json
  {
    "name": "Jane Smith",
    "email": "jane@example.com",
    "password": "securepassword456",
    "role": "analyst"
  }
  ```
- **Validation**:
  - `name`: 2-120 characters
  - `email`: Valid email, unique
  - `password`: Minimum 8 characters
  - `role`: One of `viewer`, `analyst`, `admin`
- **Response** (201 Created):
  ```json
  {
    "success": true,
    "message": "User created successfully",
    "data": {
      "id": 2,
      "name": "Jane Smith",
      "email": "jane@example.com",
      "role": "analyst",
      "is_active": true
    }
  }
  ```
- **Error Cases**:
  - `400 Bad Request`: Email already exists, invalid role
  - `403 Forbidden`: Not an admin
  - `401 Unauthorized`: Invalid token

### List Users
- **Endpoint**: `GET /api/v1/users`
- **Authentication**: Required
- **Role Required**: `admin`
- **Query Parameters**: None
- **Response** (200 OK):
  ```json
  {
    "success": true,
    "message": "Users fetched successfully",
    "data": [
      {
        "id": 1,
        "name": "John Doe",
        "email": "john@example.com",
        "role": "viewer",
        "is_active": true,
        "created_at": "2026-03-15T10:30:00+00:00"
      },
      {
        "id": 2,
        "name": "Jane Smith",
        "email": "jane@example.com",
        "role": "analyst",
        "is_active": true,
        "created_at": "2026-03-16T14:22:00+00:00"
      }
    ]
  }
  ```
- **Error Cases**:
  - `403 Forbidden`: Not an admin
  - `401 Unauthorized`: Invalid token

### Get User by ID
- **Endpoint**: `GET /api/v1/users/{user_id}`
- **Authentication**: Required
- **Role Required**: `admin`
- **Path Parameters**:
  - `user_id`: Integer, user ID
- **Response** (200 OK):
  ```json
  {
    "success": true,
    "message": "User fetched successfully",
    "data": {
      "id": 1,
      "name": "John Doe",
      "email": "john@example.com",
      "role": "viewer",
      "is_active": true,
      "created_at": "2026-03-15T10:30:00+00:00"
    }
  }
  ```
- **Error Cases**:
  - `404 Not Found`: User does not exist
  - `403 Forbidden`: Not an admin
  - `401 Unauthorized`: Invalid token

### Update User
- **Endpoint**: `PUT /api/v1/users/{user_id}`
- **Authentication**: Required
- **Role Required**: `admin`
- **Path Parameters**:
  - `user_id`: Integer, user ID
- **Request Body**:
  ```json
  {
    "name": "John D. Doe",
    "email": "john.doe@example.com",
    "password": "newsecurepassword789",
    "role": "analyst"
  }
  ```
- **Validation**:
  - `name`: Optional, 2-120 characters if provided
  - `email`: Optional, must be unique if provided
  - `password`: Optional, minimum 8 characters if provided
  - `role`: Optional, one of `viewer`, `analyst`, `admin` if provided
- **Response** (200 OK):
  ```json
  {
    "success": true,
    "message": "User updated successfully",
    "data": {
      "id": 1,
      "name": "John D. Doe",
      "email": "john.doe@example.com",
      "role": "analyst",
      "is_active": true,
      "created_at": "2026-03-15T10:30:00+00:00"
    }
  }
  ```
- **Error Cases**:
  - `404 Not Found`: User does not exist
  - `400 Bad Request`: Email already taken, invalid role
  - `403 Forbidden`: Not an admin
  - `401 Unauthorized`: Invalid token

### Update User Status
- **Endpoint**: `PATCH /api/v1/users/{user_id}/status`
- **Authentication**: Required
- **Role Required**: `admin`
- **Path Parameters**:
  - `user_id`: Integer, user ID
- **Request Body**:
  ```json
  {
    "is_active": false
  }
  ```
- **Response** (200 OK):
  ```json
  {
    "success": true,
    "message": "User status updated successfully",
    "data": {
      "id": 1,
      "name": "John Doe",
      "email": "john@example.com",
      "role": "viewer",
      "is_active": false,
      "created_at": "2026-03-15T10:30:00+00:00"
    }
  }
  ```
- **Error Cases**:
  - `404 Not Found`: User does not exist
  - `403 Forbidden`: Not an admin
  - `401 Unauthorized`: Invalid token

### Delete User
- **Endpoint**: `DELETE /api/v1/users/{user_id}`
- **Authentication**: Required
- **Role Required**: `admin`
- **Path Parameters**:
  - `user_id`: Integer, user ID
- **Response** (200 OK):
  ```json
  {
    "success": true,
    "message": "User deleted successfully",
    "data": null
  }
  ```
- **Error Cases**:
  - `404 Not Found`: User does not exist
  - `403 Forbidden`: Not an admin
  - `401 Unauthorized`: Invalid token

---

## Financial Records Endpoints

### Create Record
- **Endpoint**: `POST /api/v1/records`
- **Authentication**: Required
- **Role Required**: `admin`
- **Request Body**:
  ```json
  {
    "amount": 1500.50,
    "type": "income",
    "category": "salary",
    "date": "2026-03-20",
    "notes": "Monthly salary for March"
  }
  ```
- **Validation**:
  - `amount`: Required, greater than 0
  - `type`: Required, one of `income`, `expense`
  - `category`: Required, 2-80 characters
  - `date`: Required, valid date (YYYY-MM-DD)
  - `notes`: Optional, maximum 1000 characters
- **Response** (201 Created):
  ```json
  {
    "success": true,
    "message": "Record created successfully",
    "data": {
      "id": 1,
      "amount": 1500.50,
      "type": "income",
      "category": "salary",
      "date": "2026-03-20",
      "notes": "Monthly salary for March",
      "created_by": 1,
      "created_at": "2026-03-20T09:00:00+00:00"
    }
  }
  ```
- **Error Cases**:
  - `400 Bad Request`: Invalid amount, invalid type, invalid date format
  - `403 Forbidden`: Not an admin
  - `401 Unauthorized`: Invalid token

### List Records
- **Endpoint**: `GET /api/v1/records`
- **Authentication**: Required
- **Role Required**: `admin`, `analyst`
- **Query Parameters**:
  - `type`: Optional, filter by `income` or `expense`
  - `category`: Optional, filter by category name (substring match)
  - `start_date`: Optional, filter records on or after date (YYYY-MM-DD)
  - `end_date`: Optional, filter records on or before date (YYYY-MM-DD)
  - `notes`: Optional, filter records by notes substring
  - `page`: Optional, default 1 (page number, minimum 1)
  - `page_size`: Optional, default 10 (records per page, 1-100)
- **Response** (200 OK):
  ```json
  {
    "success": true,
    "message": "Records fetched successfully",
    "data": {
      "items": [
        {
          "id": 1,
          "amount": 1500.50,
          "type": "income",
          "category": "salary",
          "date": "2026-03-20",
          "notes": "Monthly salary for March",
          "created_by": 1,
          "created_at": "2026-03-20T09:00:00+00:00"
        },
        {
          "id": 2,
          "amount": 50.00,
          "type": "expense",
          "category": "groceries",
          "date": "2026-03-21",
          "notes": "Weekly shopping",
          "created_by": 1,
          "created_at": "2026-03-21T10:15:00+00:00"
        }
      ],
      "pagination": {
        "page": 1,
        "page_size": 10,
        "total": 2,
        "pages": 1
      }
    }
  }
  ```
- **Example Queries**:
  - Filter by income: `GET /api/v1/records?type=income`
  - Filter by date range: `GET /api/v1/records?start_date=2026-03-01&end_date=2026-03-31`
  - Search notes: `GET /api/v1/records?notes=salary&page=1&page_size=20`
  - Pagination: `GET /api/v1/records?page=2&page_size=10`
- **Error Cases**:
  - `403 Forbidden`: Not admin/analyst
  - `401 Unauthorized`: Invalid token
  - `400 Bad Request`: Invalid date format or filter values

### Get Record by ID
- **Endpoint**: `GET /api/v1/records/{record_id}`
- **Authentication**: Required
- **Role Required**: `admin`, `analyst`
- **Path Parameters**:
  - `record_id`: Integer, record ID
- **Response** (200 OK):
  ```json
  {
    "success": true,
    "message": "Record fetched successfully",
    "data": {
      "id": 1,
      "amount": 1500.50,
      "type": "income",
      "category": "salary",
      "date": "2026-03-20",
      "notes": "Monthly salary for March",
      "created_by": 1,
      "created_at": "2026-03-20T09:00:00+00:00"
    }
  }
  ```
- **Error Cases**:
  - `404 Not Found`: Record does not exist or is soft-deleted
  - `403 Forbidden`: Not admin/analyst
  - `401 Unauthorized`: Invalid token

### Update Record
- **Endpoint**: `PUT /api/v1/records/{record_id}`
- **Authentication**: Required
- **Role Required**: `admin`
- **Path Parameters**:
  - `record_id`: Integer, record ID
- **Request Body**:
  ```json
  {
    "amount": 1600.00,
    "type": "income",
    "category": "bonus",
    "date": "2026-03-22",
    "notes": "Updated salary record"
  }
  ```
- **Validation**: Same as Create Record (all fields optional)
- **Response** (200 OK):
  ```json
  {
    "success": true,
    "message": "Record updated successfully",
    "data": {
      "id": 1,
      "amount": 1600.00,
      "type": "income",
      "category": "bonus",
      "date": "2026-03-22",
      "notes": "Updated salary record",
      "created_by": 1,
      "created_at": "2026-03-20T09:00:00+00:00"
    }
  }
  ```
- **Error Cases**:
  - `404 Not Found`: Record does not exist or is soft-deleted
  - `400 Bad Request`: Invalid field values
  - `403 Forbidden`: Not an admin
  - `401 Unauthorized`: Invalid token

### Delete Record
- **Endpoint**: `DELETE /api/v1/records/{record_id}`
- **Authentication**: Required
- **Role Required**: `admin`
- **Path Parameters**:
  - `record_id`: Integer, record ID
- **Note**: Uses soft delete; record is marked deleted but not permanently removed
- **Response** (200 OK):
  ```json
  {
    "success": true,
    "message": "Record deleted successfully",
    "data": null
  }
  ```
- **Error Cases**:
  - `404 Not Found`: Record does not exist or already deleted
  - `403 Forbidden`: Not an admin
  - `401 Unauthorized`: Invalid token

---

## Dashboard Endpoints

### Dashboard Summary
- **Endpoint**: `GET /api/v1/dashboard/summary`
- **Authentication**: Required
- **Role Required**: `viewer`, `analyst`, `admin`
- **Description**: Returns total income, expenses, and net balance
- **Response** (200 OK):
  ```json
  {
    "success": true,
    "message": "Dashboard summary fetched",
    "data": {
      "total_income": 3500.00,
      "total_expense": 250.75,
      "net_balance": 3249.25
    }
  }
  ```
- **Error Cases**:
  - `403 Forbidden`: Not viewer/analyst/admin
  - `401 Unauthorized`: Invalid token

### Category Breakdown
- **Endpoint**: `GET /api/v1/dashboard/category-breakdown`
- **Authentication**: Required
- **Role Required**: `viewer`, `analyst`, `admin`
- **Description**: Returns total amount grouped by category
- **Response** (200 OK):
  ```json
  {
    "success": true,
    "message": "Category breakdown fetched",
    "data": [
      {
        "category": "groceries",
        "total": 150.50
      },
      {
        "category": "salary",
        "total": 3500.00
      },
      {
        "category": "utilities",
        "total": 100.25
      }
    ]
  }
  ```
- **Error Cases**:
  - `403 Forbidden`: Not viewer/analyst/admin
  - `401 Unauthorized`: Invalid token

### Monthly Trends
- **Endpoint**: `GET /api/v1/dashboard/monthly-trends`
- **Authentication**: Required
- **Role Required**: `viewer`, `analyst`, `admin`
- **Description**: Returns income and expense totals by month
- **Response** (200 OK):
  ```json
  {
    "success": true,
    "message": "Monthly trends fetched",
    "data": [
      {
        "month": "2026-01",
        "income": 3500.00,
        "expense": 150.50
      },
      {
        "month": "2026-02",
        "income": 3500.00,
        "expense": 200.00
      },
      {
        "month": "2026-03",
        "income": 3500.00,
        "expense": 100.25
      }
    ]
  }
  ```
- **Error Cases**:
  - `403 Forbidden`: Not viewer/analyst/admin
  - `401 Unauthorized`: Invalid token


### Weekly Trends
- **Endpoint**: `GET /api/v1/dashboard/weekly-trends`
- **Authentication**: Required
- **Role Required**: `viewer`, `analyst`, `admin`
- **Description**: Returns income and expense totals aggregated by week (ISO format).
- **Response** (200 OK):
  ```json
  {
    "success": true,
    "message": "Weekly trends fetched",
    "data": [
      {
        "week": "2026-W13",
        "income": 1200.00,
        "expense": 450.00
      }
    ]
  }
  ```````

### Recent Activity
- **Endpoint**: `GET /api/v1/dashboard/recent-activity`
- **Authentication**: Required
- **Role Required**: `viewer`, `analyst`, `admin`
- **Description**: Returns 10 most recent records
- **Response** (200 OK):
  ```json
  {
    "success": true,
    "message": "Recent activity fetched",
    "data": [
      {
        "id": 3,
        "amount": 100.25,
        "type": "expense",
        "category": "utilities",
        "date": "2026-03-21",
        "notes": "Monthly electricity bill",
        "created_by": 1,
        "created_at": "2026-03-21T14:30:00+00:00"
      },
      {
        "id": 2,
        "amount": 50.00,
        "type": "expense",
        "category": "groceries",
        "date": "2026-03-21",
        "notes": "Weekly shopping",
        "created_by": 1,
        "created_at": "2026-03-21T10:15:00+00:00"
      }
    ]
  }
  ```
- **Error Cases**:
  - `403 Forbidden`: Not viewer/analyst/admin
  - `401 Unauthorized`: Invalid token

---


### Admin Insights
- **Endpoint**: `GET /api/v1/dashboard/admin-insights`
- **Authentication**: Required
- **Role Required**: `admin`, `analyst`
- **Description**: Retrieves advanced platform-wide telemetry, including highest 30-day transaction, top 5 expenses, and rolling expense ratio.
- **Response** (200 OK):
  ```json
  {
    "success": true,
    "message": "Admin insights fetched successfully",
    "data": {
      "highest_transaction_30d": { "id": 1, "amount": 5000.0, "type": "expense" },
      "top_5_expenses": [],
      "expense_to_income_ratio": 1.25,
      "unusual_transactions": [],
      "total_income": 50000.0,
      "net_balance": 15000.0,
      "recent_transactions": []
    }
  }
  ```````

## Health Check Endpoints

### Full Health Check
- **Endpoint**: `GET /health`
- **Authentication**: Not required
- **Description**: Returns comprehensive health status including database connectivity and latency
- **Response** (200 OK):
  ```json
  {
    "success": true,
    "message": "System health check",
    "data": {
      "status": "up",
      "uptime_seconds": 3600,
      "database": {
        "status": "up",
        "latency_ms": 15.50,
        "default_roles_ready": true
      }
    }
  }
  ```
- **Response** (503 Service Unavailable - if database down):
  ```json
  {
    "success": false,
    "message": "System health check",
    "data": {
      "status": "degraded",
      "uptime_seconds": 3600,
      "database": {
        "status": "down",
        "latency_ms": null,
        "default_roles_ready": false
      }
    }
  }
  ```

### Liveness Probe
- **Endpoint**: `GET /health/liveness`
- **Description**: Returns instant app status without database check (good for orchestration startup probes)
- **Response** (200 OK):
  ```json
  {
    "success": true,
    "message": "liveness probe",
    "data": {
      "status": "up"
    }
  }
  ```

### Readiness Probe
- **Endpoint**: `GET /health/readiness`
- **Description**: Returns database availability (good for orchestration readiness gates)
- **Response** (200 OK - if ready):
  ```json
  {
    "success": true,
    "message": "readiness probe",
    "data": {
      "status": "ready"
    }
  }
  ```
- **Response** (503 Service Unavailable - if not ready):
  ```json
  {
    "success": false,
    "message": "readiness probe",
    "data": {
      "status": "not_ready",
      "reason": "database_unavailable"
    }
  }
  ```

---

## Error Code Reference

| Status | Code | Example Message | When It Occurs |
|--------|------|-----------------|----------------|
| 400 | Bad Request | Email already exists | Duplicate email, invalid input format |
| 401 | Unauthorized | Invalid credentials | Wrong password, missing/invalid token |
| 403 | Forbidden | Forbidden for this role | User lacks required role |
| 404 | Not Found | User not found | Resource doesn't exist |
| 429 | Too Many Requests | Rate limit exceeded | Too many auth requests in time window |
| 500 | Internal Server Error | Database operation failed | Database error, system configuration issue |
| 503 | Service Unavailable | Service unavailable | Database connection down |

---

## Role-Based Access Matrix

| Endpoint | Viewer | Analyst | Admin |
|----------|--------|---------|-------|
| POST /api/v1/auth/register | ✓ | ✓ | ✓ |
| POST /api/v1/auth/login | ✓ | ✓ | ✓ |
| GET /api/v1/auth/me | ✓ | ✓ | ✓ |
| POST /api/v1/users | ✗ | ✗ | ✓ |
| GET /api/v1/users | ✗ | ✗ | ✓ |
| GET /api/v1/users/{id} | ✗ | ✗ | ✓ |
| PUT /api/v1/users/{id} | ✗ | ✗ | ✓ |
| PATCH /api/v1/users/{id}/status | ✗ | ✗ | ✓ |
| DELETE /api/v1/users/{id} | ✗ | ✗ | ✓ |
| POST /api/v1/records | ✗ | ✗ | ✓ |
| GET /api/v1/records | ✗ | ✓ | ✓ |
| GET /api/v1/records/{id} | ✗ | ✓ | ✓ |
| PUT /api/v1/records/{id} | ✗ | ✗ | ✓ |
| DELETE /api/v1/records/{id} | ✗ | ✗ | ✓ |
| GET /api/v1/dashboard/summary | ✓ | ✓ | ✓ |
| GET /api/v1/dashboard/category-breakdown | ✓ | ✓ | ✓ |
| GET /api/v1/dashboard/monthly-trends | ✓ | ✓ | ✓ |
| GET /api/v1/dashboard/recent-activity | ✓ | ✓ | ✓ |

---

## Query Examples

### Filter records by income in date range
```bash
curl -H "Authorization: Bearer <token>" \
  "http://localhost:8000/api/v1/records?type=income&start_date=2026-03-01&end_date=2026-03-31&page_size=20"
```

### Search records by notes
```bash
curl -H "Authorization: Bearer <token>" \
  "http://localhost:8000/api/v1/records?notes=salary&page=1"
```

### Get paginated user list
```bash
curl -H "Authorization: Bearer <token>" \
  "http://localhost:8000/api/v1/users?page=2&page_size=50"
```

### Check system health
```bash
curl "http://localhost:8000/health"
```

---

## API Documentation UI

- **Swagger UI**: `/docs` (interactive API testing)
- **ReDoc**: `/redoc` (static documentation)


