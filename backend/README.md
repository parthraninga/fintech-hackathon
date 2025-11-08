# FinSentry Backend API

FastAPI backend for the FinSentry invoice processing platform.

## Features

- ✅ JWT Authentication & Authorization
- ✅ Role-Based Access Control (RBAC)
- ✅ Invoice Upload & Processing
- ✅ Real-time WebSocket Updates
- ✅ Dashboard Analytics & Metrics
- ✅ CSV Export Functionality
- ✅ Chat Interface with Streaming
- ✅ Batch Management
- ✅ Security (CORS, Rate Limiting, CSRF)

## Tech Stack

- **Framework:** FastAPI 0.104+
- **Database:** PostgreSQL with SQLAlchemy ORM
- **Authentication:** JWT (python-jose)
- **WebSockets:** Native FastAPI WebSocket support
- **File Processing:** Integration with existing Python scripts
- **API Docs:** Automatic OpenAPI/Swagger docs

## Installation

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# Initialize database
python init_db.py

# Run migrations (if using Alembic)
alembic upgrade head

# Start server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## Environment Variables

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/finsentry

# Security
SECRET_KEY=your-secret-key-here-generate-with-openssl-rand-hex-32
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS
FRONTEND_URL=http://localhost:5173

# File Upload
MAX_UPLOAD_SIZE=10485760  # 10MB
ALLOWED_EXTENSIONS=.pdf,.jpg,.jpeg,.png

# Rate Limiting
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_PERIOD=60
```

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login and get JWT token
- `POST /api/auth/refresh` - Refresh access token
- `GET /api/auth/me` - Get current user

### Invoice Processing
- `POST /api/invoices/upload` - Upload invoice(s)
- `GET /api/invoices` - List all invoices
- `GET /api/invoices/{id}` - Get invoice details
- `POST /api/invoices/{id}/approve` - Approve invoice
- `POST /api/invoices/{id}/reject` - Reject invoice
- `PUT /api/invoices/{id}` - Update invoice
- `DELETE /api/invoices/{id}` - Delete invoice

### Dashboard Analytics
- `GET /api/dashboard/metrics` - Get KPI metrics
- `GET /api/dashboard/vendors` - Get vendor risk data
- `GET /api/dashboard/export/csv` - Export dashboard to CSV
- `GET /api/dashboard/throughput` - Get agent throughput data
- `GET /api/dashboard/latency` - Get latency distribution

### Batch Management
- `POST /api/batches` - Create new batch
- `GET /api/batches` - List all batches
- `GET /api/batches/{id}` - Get batch details
- `GET /api/batches/{id}/status` - Get batch status

### Chat Interface
- `POST /api/chat/message` - Send chat message
- `GET /api/chat/history/{batch_id}` - Get chat history
- `WS /ws/chat` - WebSocket for streaming chat

### WebSocket Endpoints
- `WS /ws/invoices/{invoice_id}` - Real-time invoice updates
- `WS /ws/batches/{batch_id}` - Real-time batch updates
- `WS /ws/dashboard/metrics` - Real-time dashboard metrics

## Project Structure

```
backend/
├── main.py                 # FastAPI application entry point
├── config.py               # Configuration and settings
├── database.py             # Database connection and session
├── dependencies.py         # Shared dependencies (auth, etc.)
├── init_db.py             # Database initialization script
├── requirements.txt        # Python dependencies
├── .env.example           # Environment variables template
│
├── models/                # SQLAlchemy models
│   ├── __init__.py
│   ├── user.py
│   ├── invoice.py
│   ├── vendor.py
│   ├── batch.py
│   └── chat.py
│
├── schemas/               # Pydantic schemas
│   ├── __init__.py
│   ├── user.py
│   ├── invoice.py
│   ├── vendor.py
│   ├── batch.py
│   ├── dashboard.py
│   └── chat.py
│
├── routers/               # API route handlers
│   ├── __init__.py
│   ├── auth.py
│   ├── invoices.py
│   ├── dashboard.py
│   ├── batches.py
│   ├── chat.py
│   └── websockets.py
│
├── services/              # Business logic
│   ├── __init__.py
│   ├── auth_service.py
│   ├── invoice_service.py
│   ├── gst_service.py
│   ├── dashboard_service.py
│   ├── export_service.py
│   └── chat_service.py
│
├── middleware/            # Custom middleware
│   ├── __init__.py
│   ├── rate_limit.py
│   ├── csrf.py
│   └── error_handler.py
│
└── utils/                 # Utility functions
    ├── __init__.py
    ├── security.py
    ├── validators.py
    └── helpers.py
```

## Development

```bash
# Run with auto-reload
uvicorn main:app --reload

# Run tests
pytest

# Generate migration
alembic revision --autogenerate -m "description"

# Apply migration
alembic upgrade head

# Format code
black .
isort .

# Lint
flake8
mypy .
```

## API Documentation

Once the server is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI JSON: http://localhost:8000/openapi.json

## Security Features

- ✅ JWT token-based authentication
- ✅ Password hashing with bcrypt
- ✅ CORS protection
- ✅ Rate limiting per IP/user
- ✅ CSRF token validation
- ✅ SQL injection prevention (SQLAlchemy)
- ✅ File upload validation (size, type)
- ✅ Input sanitization
- ✅ Secure WebSocket connections

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_invoices.py

# Run with verbose output
pytest -v
```

## Deployment

### Docker

```bash
# Build image
docker build -t finsentry-backend .

# Run container
docker run -p 8000:8000 --env-file .env finsentry-backend
```

### Docker Compose

```bash
# Start all services (app + postgres)
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## License

Proprietary - All rights reserved
