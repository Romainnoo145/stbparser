# Offorte-Airtable Sync Agent - Test Suite

Comprehensive test suite for validating the Offorte-to-Airtable synchronization agent built with Pydantic AI.

## Test Structure

```
tests/
├── __init__.py                  # Test package marker
├── conftest.py                  # Shared fixtures and pytest configuration
├── test_settings.py             # Settings and environment configuration tests
├── test_dependencies.py         # Dependency injection tests
├── test_tools.py                # All 6 tool function tests
├── test_agent.py                # Agent initialization and tool registration tests
├── test_server.py               # FastAPI webhook server tests
├── test_integration.py          # End-to-end integration tests
├── VALIDATION_REPORT.md         # Comprehensive validation report
└── README.md                    # This file
```

## Test Categories

### Unit Tests (70+ tests)
Tests individual functions and modules in isolation.

**Coverage**:
- Settings loading and validation
- Dependency injection
- Webhook signature validation
- Data parsing and transformation
- Invoice split calculations
- Element parsing logic

**Run**: `pytest -m unit`

### Integration Tests (25+ tests)
Tests complete workflows with mocked external services.

**Coverage**:
- End-to-end webhook → sync flow
- Multi-table synchronization
- Error recovery and retries
- Validation gates from PRP

**Run**: `pytest -m integration`

### Performance Tests (5 tests)
Tests speed and efficiency requirements.

**Coverage**:
- Webhook response time < 1 second
- Batch operation limits
- Rate limiting compliance
- Processing time tracking

**Run**: `pytest -m slow`

### Dutch Language Tests (8 tests)
Tests Dutch-specific formatting and characters.

**Coverage**:
- Special characters (ë, ï, ö, ü, €)
- Number formatting (1.234,56)
- City names ('s-Hertogenbosch)
- Invoice labels (vooraf, bij start, oplevering)

**Run**: `pytest -m dutch`

### Security Tests (6 tests)
Tests security measures and validations.

**Coverage**:
- HMAC signature validation
- Constant-time comparison
- API key protection
- Input validation

**Run**: `pytest -m security`

## Running Tests

### Prerequisites

```bash
# Install dependencies
pip install -r requirements.txt

# Install test dependencies
pip install pytest pytest-asyncio pytest-mock pytest-cov
```

### Basic Test Execution

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_tools.py

# Run specific test class
pytest tests/test_tools.py::TestValidateWebhook

# Run specific test function
pytest tests/test_tools.py::TestValidateWebhook::test_validate_webhook_valid_signature
```

### Test Categories

```bash
# Run unit tests only
pytest -m unit

# Run integration tests only
pytest -m integration

# Run Dutch language tests
pytest -m dutch

# Run fast tests (exclude slow)
pytest -m "not slow"

# Run multiple markers
pytest -m "unit or integration"
```

### Coverage Reports

```bash
# Run with coverage
pytest --cov=offorte_airtable_sync

# Generate HTML coverage report
pytest --cov=offorte_airtable_sync --cov-report=html

# Open coverage report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

### Parallel Execution

```bash
# Install pytest-xdist
pip install pytest-xdist

# Run tests in parallel (4 workers)
pytest -n 4

# Run tests with auto-detected CPU count
pytest -n auto
```

## Test Fixtures

### Settings Fixtures

- `test_settings`: Complete Settings object with test values
- `test_deps`: AgentDependencies from test_settings

### Model Fixtures

- `test_model`: Pydantic AI TestModel for fast validation
- `test_agent_with_test_model`: Agent with TestModel override
- `function_model_simple`: FunctionModel with simple responses
- `function_model_with_tools`: FunctionModel that simulates tool calling

### Mock Data Fixtures

- `mock_offorte_proposal`: Sample proposal data
- `mock_offorte_company`: Sample company data
- `mock_offorte_contact`: Sample contact data
- `mock_offorte_content`: Sample proposal content with elements
- `mock_webhook_payload`: Sample webhook event
- `mock_airtable_record`: Sample Airtable record response

### HTTP Fixtures

- `mock_http_client`: AsyncMock HTTP client
- `mock_redis_client`: AsyncMock Redis client

### Dutch Language Fixtures

- `dutch_special_chars`: Dutch special characters test data
- `dutch_invoice_splits`: Expected invoice split calculations

## Environment Setup

### Test Environment Variables

Create a `.env.test` file:

```env
# Offorte Configuration
OFFORTE_API_KEY=test_offorte_key
OFFORTE_ACCOUNT_NAME=test_account

# Airtable Configuration
AIRTABLE_API_KEY=test_airtable_key
AIRTABLE_BASE_ADMINISTRATION=appTestAdmin123
AIRTABLE_BASE_SALES_REVIEW=appTestSales123
AIRTABLE_BASE_TECHNISCH=appTestTech123

# LLM Configuration
LLM_API_KEY=test_llm_key
LLM_MODEL=gpt-4o

# Server Configuration
WEBHOOK_SECRET=test_webhook_secret_12345
SERVER_PORT=8000

# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# Application Settings
APP_ENV=testing
LOG_LEVEL=DEBUG
DEBUG=true
```

### Load Test Environment

```bash
# Export variables
export $(cat .env.test | xargs)

# Or use python-dotenv
python -c "from dotenv import load_dotenv; load_dotenv('.env.test')"
```

## Validation Gates

The test suite validates all success criteria from the PRP:

### ✅ Gate 1: Webhook Response < 1 Second
**Test**: `test_validation_gate_webhook_response_time`
**Status**: PASSED

### ✅ Gate 2: All 6 Tables Sync Correctly
**Test**: `test_validation_gate_all_six_tables_sync`
**Status**: PASSED

### ✅ Gate 3: Invoice Splits (30/65/5)
**Test**: `test_validation_gate_invoice_splits_30_65_5`
**Status**: PASSED

### ✅ Gate 4: Coupled Elements Separate Records
**Test**: `test_validation_gate_coupled_elements_separate_records`
**Status**: PASSED

### ✅ Gate 5: No Duplicate Records on Re-sync
**Test**: `test_validation_gate_no_duplicate_records_on_resync`
**Status**: PASSED

### ✅ Gate 6: Dutch Special Characters
**Test**: `test_validation_gate_dutch_special_characters`
**Status**: PASSED

## Continuous Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v2

    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.11'

    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-asyncio pytest-cov

    - name: Run tests
      run: pytest --cov=offorte_airtable_sync --cov-report=xml

    - name: Upload coverage
      uses: codecov/codecov-action@v2
```

## Troubleshooting

### Common Issues

#### Import Errors

```bash
# Add parent directory to Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Or use pytest with proper path
pytest --import-mode=importlib
```

#### Async Test Failures

```bash
# Ensure pytest-asyncio is installed
pip install pytest-asyncio

# Check pytest.ini has asyncio_mode = auto
```

#### Mock Issues

```bash
# Ensure pytest-mock is installed
pip install pytest-mock

# Or use unittest.mock directly
from unittest.mock import Mock, AsyncMock, patch
```

#### Fixture Not Found

```bash
# Ensure conftest.py is in tests/ directory
# Check fixture names match exactly
# Verify fixture scope (function, class, module, session)
```

## Best Practices

### Writing New Tests

1. **Use Descriptive Names**: `test_webhook_validates_signature_correctly`
2. **One Assert Per Concept**: Focus on single behavior
3. **Use Fixtures**: Reuse test data and setup
4. **Mark Appropriately**: Add `@pytest.mark.unit` or similar
5. **Mock External Services**: Don't make real API calls
6. **Test Happy Path and Edge Cases**: Both success and failure
7. **Document Complex Tests**: Add docstrings explaining what's tested

### Test Organization

```python
class TestFeatureX:
    """Group related tests together."""

    def test_feature_x_success(self):
        """Test successful feature X execution."""
        pass

    def test_feature_x_validation_error(self):
        """Test feature X handles validation errors."""
        pass

    def test_feature_x_with_edge_case(self):
        """Test feature X with edge case input."""
        pass
```

### Async Test Pattern

```python
@pytest.mark.asyncio
async def test_async_function(test_deps):
    """Test async function with dependencies."""
    result = await async_function(test_deps)
    assert result is not None
```

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Pydantic AI Testing Guide](https://ai.pydantic.dev/testing/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [PRP Document](../Offorte-Airtable-Sync-Agent-PRP.md)
- [Validation Report](./VALIDATION_REPORT.md)

## Contributing

When adding new features:

1. Write tests first (TDD)
2. Ensure all existing tests pass
3. Add integration tests for new workflows
4. Update VALIDATION_REPORT.md if adding validation gates
5. Run full test suite before committing

## Support

For questions or issues with tests:

1. Check VALIDATION_REPORT.md for validation status
2. Review conftest.py for available fixtures
3. Check pytest output for detailed error messages
4. Review individual test files for examples

---

**Test Suite Version**: 1.0.0
**Last Updated**: 2025-01-07
**Total Tests**: 115+
**Coverage Target**: 90%+
