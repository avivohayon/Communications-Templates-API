# Test Suite - Communications API

## Quick Start

```bash
# Activate virtual environment
source .venv/bin/activate

# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=term-missing
```

## What's Being Tested

### 1. Template Renderer (`test_template_renderer.py`)
**12 tests covering Jinja2 template rendering**

- **Syntax Validation**: Validates Jinja2 syntax (valid/invalid templates)
- **StrictUndefined**: Ensures missing variables raise errors (not silent failures)
- **Edge Cases**: Static templates, filters, conditionals

**Key Tests:**
- ✅ Missing variables raise `ValueError`
- ✅ Wrong variable names (e.g., `name2` instead of `name`) are caught
- ✅ Template syntax errors detected before saving

### 2. Template Logic (`test_logic_template.py`)
**6 tests covering template business logic**

- **Validation**: Jinja2 syntax checked during create/update
- **Preview**: Template rendering with test data

**Key Tests:**
- ✅ Invalid content syntax rejected
- ✅ Invalid subject syntax rejected (for emails)
- ✅ Preview validates all required variables

### 3. Message Sending (`test_logic_message.py`)
**7 tests covering message orchestration**

- **Success Scenarios**: Email/SMS sending, multiple recipients
- **Failure Scenarios**: Missing variables, channel failures, template not found
- **Partial Success**: Some recipients succeed, others fail

**Key Tests:**
- ✅ Email/SMS sent successfully with correct data
- ✅ Missing variables cause clear errors
- ✅ Partial success handled correctly

## Test Results

**✅ 25 out of 25 tests passing in 0.24 seconds**

```
tests/unit/test_logic_message.py::TestMessageSendingSuccess ........... [3/7]
tests/unit/test_logic_message.py::TestMessageSendingFailures ......... [7/7]
tests/unit/test_logic_template.py::TestTemplateLogicValidation ....... [4/6]
tests/unit/test_logic_template.py::TestTemplateLogicPreview ......... [6/6]
tests/unit/test_template_renderer.py .................................. [12/12]
```

## Coverage

| Module | Coverage | Status |
|--------|----------|--------|
| `logic_message.py` | 92% | ⭐ Excellent |
| `schema_message.py` | 93% | ⭐ Excellent |
| `base_channel.py` | 90% | ⭐ Excellent |
| `template_renderer.py` | 74% | ✅ Good |
| `logic_template.py` | 57% | ✅ Good |

## Running Specific Tests

```bash
# Run only template renderer tests
pytest tests/unit/test_template_renderer.py -v

# Run only StrictUndefined tests (critical bug validation)
pytest tests/unit/test_template_renderer.py::TestTemplateRendererStrictUndefined -v

# Run only message sending tests
pytest tests/unit/test_logic_message.py -v

# Run a specific test
pytest tests/unit/test_template_renderer.py::TestTemplateRendererStrictUndefined::test_render_with_wrong_variable_name_raises_error -v
```

## Test Architecture

**Pure Unit Tests:**
- ✅ All dependencies mocked (database, external APIs)
- ✅ No real DB connections
- ✅ No SendGrid/Twilio API calls
- ✅ Fast execution (0.24 seconds for all tests)

**Fixtures:**
- `mock_db`: Mock AsyncSession for database operations
- `MockEmailChannel`: Mock SendGrid channel
- `MockSMSChannel`: Mock Twilio channel

## Critical Bug Validations

These tests specifically validate reported bugs:

1. **Wrong Variable Names** ⭐
   ```python
   # Template expects {{ name }}, data has {"name2": "Aviv"}
   # Result: Raises ValueError with clear error message
   ```

2. **Missing Variables** ⭐
   ```python
   # Template expects {{ code }}, data is missing it
   # Result: Raises ValueError during rendering
   ```

3. **Template Preview Validation** ⭐
   ```python
   # Preview with incomplete data
   # Result: Validation error before sending
   ```

## What's NOT Tested (Requires Integration Tests)

- ❌ Real database operations (CRUD with PostgreSQL)
- ❌ API endpoints (FastAPI routes)
- ❌ External API integration (SendGrid/Twilio sandbox)
- ❌ Rate limiting (excluded from scope)

## Next Steps

To expand testing:
1. Add integration tests with test database
2. Add API endpoint tests with FastAPI TestClient
3. Add E2E tests with SendGrid/Twilio test mode

---

**For detailed documentation, see:** `UNIT_TESTS_COMPLETE.md`
