# Tests

Automated test suite for the Image Search AI Router.

## Test Structure

```
tests/
├── __init__.py
├── test_infrastructure.py    # Unit tests for core components
├── test_load.py               # Load testing and stress tests
└── README.md                  # This file
```

## CI/CD Safe Tests

All tests in this directory are **safe to run in CI/CD pipelines**:

✅ No API keys required  
✅ Uses mock providers  
✅ No external dependencies  
✅ Fast execution (<30 seconds total)  
✅ Deterministic results  

## Running Tests

### Option 1: Run All Tests

```powershell
# From project root
python -m pytest tests/ -v

# Or run directly
python tests/test_infrastructure.py
python tests/test_load.py
```

### Option 2: Run Specific Test File

```powershell
# Infrastructure tests (utilities, rate limiter, mock provider)
python tests/test_infrastructure.py

# Load tests (rate limiter, circuit breaker, concurrency)
python tests/test_load.py
```

### Option 3: Using pytest

```powershell
# Install pytest if needed
pip install pytest

# Run all tests with verbose output
pytest tests/ -v

# Run specific test file
pytest tests/test_infrastructure.py -v

# Run with coverage
pytest tests/ --cov=apps --cov-report=html
```

## Test Coverage

### test_infrastructure.py (4 tests)
- ✅ Image utility functions (encode, validate, metadata)
- ✅ Rate limiter (limits, budget, stats)
- ✅ Mock cloud provider (captions, cost, latency)
- ✅ Provider factory (creation, defaults)

### test_load.py (4 tests)
- ✅ Rate limiter under sustained load
- ✅ Circuit breaker fault tolerance
- ✅ Concurrent request handling
- ✅ Error recovery

**Total: 8 tests, all CI/CD safe**

## Expected Output

### Successful Run
```
============================================================
INFRASTRUCTURE TESTS (CI/CD Safe)
============================================================

✅ PASS  Image Utilities
✅ PASS  Rate Limiter
✅ PASS  Mock Provider
✅ PASS  Provider Factory

4/4 tests passed

🎉 All infrastructure tests passed!
✓ Safe to run in CI/CD pipeline
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -r apps/api/requirements.txt
          pip install pytest
      - name: Run tests
        run: pytest tests/ -v
```

### GitLab CI Example

```yaml
test:
  stage: test
  script:
    - pip install -r apps/api/requirements.txt
    - pip install pytest
    - pytest tests/ -v
```

## Test Configuration

Tests automatically:
- ✅ Handle path resolution (work from anywhere)
- ✅ Configure UTF-8 encoding for Windows
- ✅ Use mock providers (no real API calls)
- ✅ Clean up after themselves
- ✅ Provide detailed output

## Additional Test Files

Other test files in the project (require API keys or running services):

```
test_scripts/               # Manual testing scripts
test_phase2_openrouter.py  # Requires OPENROUTER_API_KEY
test_model_comparison.py   # Requires OPENROUTER_API_KEY
test_end_to_end.py         # Requires running API server
```

These are **NOT** suitable for CI/CD but useful for:
- Local development
- Integration testing
- Performance benchmarking
- Model comparison

## Troubleshooting

### Import Errors
Tests automatically add project root to Python path. If you get import errors:
```powershell
# Make sure you're running from project root
cd C:\Users\firou\PycharmProjects\ImageSearch
python tests/test_infrastructure.py
```

### Encoding Errors on Windows
Tests handle UTF-8 encoding automatically. If you see encoding errors, they're ignored in CI environments.

### Slow Tests
The mock provider simulates 1-3 second latency. This is intentional to test async behavior. Total test time: ~20-30 seconds.

## Contributing

When adding new tests:
1. ✅ Ensure they don't require API keys
2. ✅ Use mock providers for cloud services
3. ✅ Add to appropriate test file
4. ✅ Update this README
5. ✅ Verify they pass in CI/CD
