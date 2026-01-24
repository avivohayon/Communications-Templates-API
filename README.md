# Communications API

A FastAPI-based RESTful API for managing message templates and sending messages via Email (SendGrid) and SMS (Twilio).

## 🎯 Features

### ✅ Implemented
- **Template Management**: Create, read, update, delete message templates (Email & SMS)
- **Class Table Inheritance**: Clean database design with polymorphic templates
- **Jinja2 Templating**: Dynamic variable substitution in messages
- **Message Channels**: SendGrid (Email) and Twilio (SMS) integrations
- **Rate Limiting**: Configurable per-recipient message quotas
- **Soft Deletion**: Data preservation for audit trails

### 🚧 In Progress
- Message sending orchestration
- Message history tracking
- Template preview endpoint

## 🏗️ Architecture

This project follows a clean 3-layer architecture:

```
API Layer (FastAPI routers)
    ↓
Logic Layer (Business rules, validation)
    ↓
Data Access Layer (Database operations)
    ↓
PostgreSQL Database
```

## 🚀 Quick Start

### Prerequisites
- Python 3.13+
- Docker & Docker Compose (for PostgreSQL)
- SendGrid API Key
- Twilio Account SID & Auth Token

### Installation

1. **Clone the repository**
   ```bash
   cd Aviv-Ohayon_communications-api-exercise/
   ```

2. **Create virtual environment**
   ```bash
   python3.13 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp env_template.txt .env
   # Edit .env with your credentials
   ```

5. **Start PostgreSQL**
   ```bash
   docker-compose up -d
   ```

6. **Run database migrations**
   ```bash
   # Connect to PostgreSQL and run SQL files in src/migrations/ in order:
   # 001_create_templates.sql
   # 002_create_message_history.sql
   # 003_create_rate_limits.sql
   ```

7. **Start the server**
   ```bash
   python run_server.py
   ```

8. **Access API documentation**
   ```
   http://localhost:8002/docs
   ```

## 📚 API Endpoints

### Template Management

#### Create Template
```bash
POST /templates/

# Email template
{
  "name": "welcome_email",
  "channel_type": "email",
  "subject": "Welcome {{name}}!",
  "content": "<h1>Hello {{name}}</h1>"
}

# SMS template
{
  "name": "verification_sms",
  "channel_type": "sms",
  "content": "Your code is {{code}}"
}
```

#### Get Template by ID
```bash
GET /templates/{template_id}
```

#### Get Template by Name
```bash
GET /templates/by-name/{name}
```

#### List All Templates
```bash
GET /templates/?skip=0&limit=100
```

#### Update Template
```bash
PUT /templates/{template_id}
{
  "subject": "Welcome aboard, {{name}}!"
}
```

#### Delete Template
```bash
DELETE /templates/{template_id}
```

### Message Sending (Coming Soon)
```bash
POST /messages/send
{
  "template_name": "welcome_email",
  "data": {"name": "John"},
  "to": ["user@example.com"]
}
```

## 🗄️ Database Schema

### Class Table Inheritance Design

**Templates:**
```
templates (base)
  ├─→ email_templates (content, subject)
  └─→ sms_templates (content)
```

**Message History:**
```
message_history (base)
  ├─→ email_message_history (rendered_content, rendered_subject, sendgrid_id)
  └─→ sms_message_history (rendered_content, twilio_sid)
```

**Rate Limits:**
```
rate_limits (recipient, message_count, window_start)
```

## 🧪 Testing

### Run Tests
```bash
pytest -v
```

### Test Template CRUD
```bash
# Create email template
curl -X POST http://localhost:8002/templates/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "test_email",
    "channel_type": "email",
    "subject": "Test {{variable}}",
    "content": "<p>Hello {{variable}}</p>"
  }'
```

## 📖 Configuration

### Environment Variables

Create a `.env` file with:

```env
# Database
DATABASE_URL=postgresql+asyncpg://user123:pwd123@localhost:5555/project_db
POSTGRES_USER=user123
POSTGRES_PASSWORD=pwd123
POSTGRES_DB=project_db

# SendGrid (Email)
SENDGRID_API_KEY=your_api_key_here
SENDGRID_FROM_EMAIL=your_email@example.com

# Twilio (SMS)
TWILIO_ACCOUNT_SID=your_account_sid_here
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_FROM_NUMBER=+15005550006

# Application
LOG_LEVEL=INFO
ENVIRONMENT=development

# Rate Limiting
MAX_MESSAGES_PER_RECIPIENT_PER_HOUR=5
```

## 🏛️ Project Structure

```
src/
├── api/                # FastAPI routers
├── logic/              # Business logic layer
├── das/                # Data access layer
├── models/             # SQLAlchemy models
├── schemas/            # Pydantic schemas
├── services/           # External services (SendGrid, Twilio, etc.)
├── migrations/         # SQL migration files
├── config.py           # Configuration management
├── database.py         # Database session management
└── main.py             # FastAPI application
```

## 💡 Key Design Decisions

1. **Class Table Inheritance (CTI)**: Separate tables for email vs SMS templates to avoid sparse columns and enable extensibility.

2. **Jinja2 Templates**: Powerful templating engine with variable substitution, filters, and control structures.

3. **3-Layer Architecture**: Clean separation between API, business logic, and data access for maintainability and testability.

4. **Async All the Way**: Leverages Python's asyncio for better I/O performance.

5. **Soft Deletion**: Preserves data for audit trails and regulatory compliance.

6. **UTC Timestamps**: All timestamps stored as Unix timestamps (integers) in UTC for consistency.

## 🛠️ Technology Stack

- **Framework**: FastAPI
- **Database**: PostgreSQL
- **ORM**: SQLAlchemy (async)
- **Validation**: Pydantic
- **Templating**: Jinja2
- **Email**: SendGrid API
- **SMS**: Twilio API
- **Testing**: pytest, httpx

## 📝 License

This is a home assignment project for LendBuzz technical interview.

## 👤 Author

Aviv Ohayon

## 🙏 Acknowledgments

- Inspired by the `python_home_assignment` architecture
- Built following the `SERVER_SETUP_INSTRUCTIONS.md` best practices
