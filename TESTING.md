# AI Pal Testing Guide

Comprehensive testing guide for the AI Pal project.

## Table of Contents

1. [Overview](#overview)
2. [Test Structure](#test-structure)
3. [Running Tests](#running-tests)
4. [Writing Tests](#writing-tests)
5. [Test Coverage](#test-coverage)
6. [CI/CD Integration](#cicd-integration)

## Overview

AI Pal uses a comprehensive testing strategy with three test levels:

- **Unit Tests**: Fast, isolated tests of individual components
- **Integration Tests**: Tests of component interactions
- **E2E Tests**: Complete workflow tests

Testing is critical for AI Pal because we implement ethical constraints that must be verified.

## Test Structure

```
tests/
├── conftest.py                    # Shared fixtures and configuration
├── unit/                          # Unit tests (fast, isolated)
│   ├── test_plugin_manager.py   # Plugin system tests
│   └── test_credentials.py       # Credential management tests
├── integration/                   # Integration tests
│   ├── test_four_gates_integration.py  # Four Gates workflow
│   └── test_aho_tribunal.py      # AHO Tribunal tests
└── e2e/                          # End-to-end tests
    └── test_complete_workflow.py
```

## Running Tests

### Install Test Dependencies

```bash
pip install -r requirements-test.txt
```

### Run All Tests

```bash
pytest
```

### Run Specific Test Types

```bash
# Unit tests only (fast)
pytest -m unit

# Integration tests
pytest -m integration

# E2E tests
pytest -m e2e

# Skip slow tests
pytest -m "not slow"
```

### Run Specific Test Files

```bash
# Test plugin manager
pytest tests/unit/test_plugin_manager.py

# Test credentials
pytest tests/unit/test_credentials.py

# Test Four Gates
pytest tests/integration/test_four_gates_integration.py

# Test AHO Tribunal
pytest tests/integration/test_aho_tribunal.py
```

### Run Specific Test Functions

```bash
pytest tests/unit/test_plugin_manager.py::test_plugin_manager_initialization
pytest tests/unit/test_credentials.py::test_store_credential -v
```

### Run with Coverage

```bash
# Run with coverage report
pytest --cov=src/ai_pal --cov-report=term-missing

# Generate HTML coverage report
pytest --cov=src/ai_pal --cov-report=html
open htmlcov/index.html
```

### Run in Parallel

```bash
# Install pytest-xdist
pip install pytest-xdist

# Run tests in parallel
pytest -n auto
```

## Writing Tests

### Test Organization

1. **One test file per source file**: `plugin_manager.py` → `test_plugin_manager.py`
2. **Descriptive test names**: `test_plugin_freeze_on_gate_failure`
3. **Use appropriate markers**: `@pytest.mark.unit`, `@pytest.mark.integration`

### Using Fixtures

Fixtures are defined in `conftest.py` and available in all tests.

```python
@pytest.mark.unit
def test_using_fixtures(plugin_manager, sample_plugin_manifest):
    """Test using provided fixtures."""
    plugin_manager.discovered_plugins["test"] = sample_plugin_manifest
    assert "test" in plugin_manager.discovered_plugins
```

### Available Fixtures

#### Core Fixtures

- `temp_dir` - Temporary directory (auto-cleaned)
- `temp_plugins_dir` - Temporary plugins directory
- `temp_credentials_file` - Temporary credentials file
- `temp_reports_dir` - Temporary reports directory

#### Component Fixtures

- `plugin_manager` - Pre-configured PluginManager
- `credential_manager` - Pre-configured SecureCredentialManager
- `ethics_module` - Initialized EthicsModule
- `mock_module` - Mock BaseModule for testing
- `sample_appeal` - Sample AHO Appeal

#### Test Data Fixtures

- `sample_plugin_manifest` - Plugin manifest
- `sample_credentials` - Sample credential dict
- `vulnerable_user_profiles` - Diverse user profiles
- `generate_test_users` - Factory for generating test users

#### Utility Fixtures

- `timer` - Performance timing
- `assert_agency_delta` - Agency assertion helper
- `assert_disparity_ratio` - Disparity assertion helper

### Async Tests

Use `@pytest.mark.asyncio` for async tests:

```python
@pytest.mark.asyncio
async def test_async_function(ethics_module):
    """Test async functionality."""
    result = await ethics_module.measure_agency_impact("action", {})
    assert result.net_agency_delta >= 0.0
```

### Parametrized Tests

Test multiple scenarios efficiently:

```python
@pytest.mark.parametrize("permission,expected", [
    (PluginPermission.READ_USER_DATA, True),
    (PluginPermission.EXECUTE_CODE, False),
])
def test_permissions(plugin_manager, permission, expected):
    """Test different permission scenarios."""
    granted = plugin_manager.check_permission("plugin", permission)
    assert granted == expected
```

## Test Markers

Use markers to categorize tests:

```python
@pytest.mark.unit           # Fast, isolated unit test
@pytest.mark.integration    # Integration test
@pytest.mark.e2e           # End-to-end test
@pytest.mark.slow          # Slow test (skip in quick runs)
@pytest.mark.asyncio       # Async test
```

Run specific markers:

```bash
pytest -m unit              # Only unit tests
pytest -m "not slow"        # Skip slow tests
pytest -m "unit or integration"  # Unit OR integration
```

## Test Coverage

### Coverage Goals

- **Overall**: 70%+ coverage (enforced by pytest.ini)
- **Core Components**: 80%+ coverage
  - Plugin Manager: 85%+
  - Credential Manager: 85%+
  - Ethics Module: 90%+
  - Four Gates: 95%+

### View Coverage Report

```bash
# Terminal report
pytest --cov=src/ai_pal --cov-report=term

# HTML report
pytest --cov=src/ai_pal --cov-report=html
open htmlcov/index.html

# XML report (for CI/CD)
pytest --cov=src/ai_pal --cov-report=xml
```

### Coverage Configuration

Coverage is configured in `pytest.ini`:

```ini
[coverage:run]
source = src/ai_pal
omit = */tests/*, */conftest.py

[coverage:report]
fail_under = 70
show_missing = True
```

## CI/CD Integration

Tests run automatically in GitHub Actions via `.github/workflows/four-gates.yml`.

### Local CI/CD Simulation

```bash
# Run the same tests as CI/CD
pytest tests/gates/ -v

# Check if all gates pass
python -m ai_pal.tests.gates.gate1_net_agency
python -m ai_pal.tests.gates.gate2_extraction_static
python -m ai_pal.tests.gates.gate3_humanity_override
python -m ai_pal.tests.gates.gate4_performance_parity

# Check for pass flags
ls -la reports/
# Should see: gate1_pass.flag, gate2_pass.flag, etc.
```

### CI/CD Test Requirements

All tests must pass before deployment:

- ✅ Unit tests (70%+ coverage)
- ✅ Integration tests
- ✅ Four Gates tests
- ✅ Code quality checks (black, ruff, mypy)

## Test Examples

### Unit Test Example

```python
@pytest.mark.unit
def test_plugin_freeze(plugin_manager):
    """Test freezing a plugin (governance with teeth)."""
    result = plugin_manager.freeze_plugin(
        "bad_plugin",
        reason="Gate 2 violation"
    )

    assert result is True
    assert "bad_plugin" in plugin_manager.frozen_plugins
```

### Integration Test Example

```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_complete_four_gates(ethics_module):
    """Test complete Four Gates workflow."""
    context = {
        "task_efficacy": 0.8,
        "bhir": 1.3,
        "reversible": True,
    }

    result = await ethics_module.run_four_gates("action", context)

    assert result.overall_pass is True
    assert len(result.blocking_gates) == 0
```

### API Test Example

```python
@pytest.mark.integration
def test_aho_override_step(client, sample_appeal):
    """Test Override step of Override-Restore-Repair."""
    db.add_appeal(sample_appeal)

    response = client.post(
        f"/api/appeals/{sample_appeal.appeal_id}/override",
        json={
            "reviewer_id": "reviewer_001",
            "decision": "approve",
            "notes": "Approved",
        }
    )

    assert response.status_code == 200
    assert response.json()["next_step"] == "restore"
```

## Debugging Tests

### Run Single Test in Verbose Mode

```bash
pytest tests/unit/test_plugin_manager.py::test_freeze_plugin -vv
```

### Drop into Debugger on Failure

```bash
pytest --pdb
```

### Show Print Statements

```bash
pytest -s
```

### Show Local Variables on Failure

```bash
pytest -l
```

## Performance Testing

Use the `timer` fixture for performance tests:

```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_gate_performance(ethics_module, timer):
    """Test gate performance."""
    timer.start()
    await ethics_module.run_four_gates("action", {})
    timer.stop()

    assert timer.elapsed_ms < 100  # Should complete in 100ms
```

## Best Practices

1. **Test Behavior, Not Implementation**: Test what code does, not how
2. **One Assertion Per Test** (guideline): Focus on one thing
3. **Use Descriptive Names**: `test_plugin_freeze_on_gate_failure` > `test_freeze`
4. **Arrange-Act-Assert**: Structure tests clearly
5. **Use Fixtures**: Don't repeat setup code
6. **Mark Tests**: Use `@pytest.mark.*` appropriately
7. **Test Error Cases**: Test failures, not just success
8. **Keep Tests Fast**: Unit tests < 10ms, integration < 100ms
9. **Avoid Test Interdependence**: Tests should run in any order
10. **Clean Up**: Use fixtures that auto-clean (temp_dir, etc.)

## Troubleshooting

### Tests Fail Locally But Pass in CI

- Check Python version (`python --version`)
- Check installed dependencies (`pip freeze`)
- Clear pytest cache: `pytest --cache-clear`
- Remove `__pycache__`: `find . -type d -name __pycache__ -exec rm -rf {} +`

### Coverage Lower Than Expected

- Run with `--cov-report=html` to see what's missing
- Check if files are being imported correctly
- Verify `[coverage:run]` configuration in `pytest.ini`

### Async Tests Not Running

- Install `pytest-asyncio`: `pip install pytest-asyncio`
- Add `@pytest.mark.asyncio` decorator
- Check `asyncio_mode = auto` in `pytest.ini`

### Fixtures Not Found

- Check fixture is defined in `conftest.py`
- Verify `conftest.py` is in correct directory
- Check fixture scope matches usage

## Contributing Tests

When contributing code, include tests:

1. **Unit tests** for all new functions/methods
2. **Integration tests** for component interactions
3. **Update fixtures** if adding new test utilities
4. **Maintain coverage** at 70%+
5. **Run tests locally** before pushing

```bash
# Before committing
pytest
black .
ruff check .
mypy src/
```

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Pytest-Asyncio](https://pytest-asyncio.readthedocs.io/)
- [Coverage.py](https://coverage.readthedocs.io/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)

---

**Testing is not optional - it's how we ensure AI Pal expands human agency safely.**
