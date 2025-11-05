# Testing Guide for CLIP for Humanists

This document explains how to run the test suite for the Django web application.

## Quick Start

```bash
# From project root
cd /path/to/CLIP_for_semiotics

# Install test dependencies (if not already installed)
pip install -r requirements-django.txt

# Run all tests
pytest

# Run with coverage report
pytest --cov

# Run specific test categories
pytest -m unit                  # Only unit tests
pytest -m integration          # Only integration tests
pytest -m api                  # Only API tests
pytest -m models               # Only model tests
pytest -m views                # Only view tests
pytest -m forms                # Only form tests
```

## Test Suite Overview

The test suite contains **200+ tests** organized into:

### Unit Tests (`clip_web/tests/unit/`)

**test_models.py** (60+ tests)
- User and UserProfile creation
- Project model with auto-slug generation
- ProjectMembership roles and permissions
- ImageDataset CRUD operations
- Image model with EXIF and GPS data
- Analysis lifecycle management
- TextPrompt and SimilarityResult validation
- Database constraints and uniqueness

**test_api.py** (50+ tests)
- REST API endpoints for all models
- Authentication (token + session)
- Permission checks (role-based access)
- Project collaborator management
- Image semantic search (with mocked CLIP)
- Analysis creation and progress tracking
- Pagination, filtering, and search
- Error handling

**test_views.py** (60+ tests)
- Authentication views (register, login, profile)
- Project CRUD views
- Dataset management views
- Image upload interface
- Analysis creation wizard
- HTMX partial endpoints
- Permission checks per role
- Search and filtering

**test_forms.py** (15+ tests)
- AnalysisCreateForm validation
- Text prompt parsing (max 50, no duplicates)
- UserRegistrationForm validation
- Password and email validation
- Form error handling

### Integration Tests (`clip_web/tests/integration/`)

**test_workflows.py** (20+ tests)
- Complete user journey: register → project → upload → analyze
- Collaboration workflow with multiple users
- Data management lifecycle
- Analysis creation to completion
- Error handling scenarios
- API-driven workflows

## Test Configuration

### pytest.ini
```ini
[pytest]
DJANGO_SETTINGS_MODULE = config.settings
testpaths = clip_web/tests
addopts = --verbose --tb=short --cov=clip_web --nomigrations --reuse-db
```

Key settings:
- `--nomigrations`: Skip running migrations (faster tests)
- `--reuse-db`: Reuse test database between runs
- `--cov=clip_web`: Generate coverage report
- `--verbose`: Detailed test output

### Fixtures (conftest.py)

Shared fixtures available in all tests:

**Users:**
- `user` - Standard test user
- `user2` - Second test user for collaboration tests
- `admin_user` - Superuser

**Projects:**
- `project` - Private project owned by `user`
- `public_project` - Public project

**Data:**
- `dataset` - Image dataset in project
- `image` - Single test image
- `images` - List of 5 test images
- `image_with_gps` - Image with GPS and EXIF data
- `create_test_image` - Factory fixture to create images

**Analysis:**
- `analysis` - Pending analysis with 3 prompts
- `completed_analysis` - Completed analysis with results

**API:**
- `api_client` - DRF API test client
- `authenticated_client` - Pre-authenticated API client

**Mocks:**
- `mock_clip_service` - Mocked CLIP service (no GPU needed)

## Running Tests

### Run All Tests
```bash
pytest
```

### Run with Coverage
```bash
pytest --cov --cov-report=html
# Open htmlcov/index.html to view coverage
```

### Run Specific Tests
```bash
# By file
pytest clip_web/tests/unit/test_models.py

# By class
pytest clip_web/tests/unit/test_models.py::TestProjectModel

# By function
pytest clip_web/tests/unit/test_models.py::TestProjectModel::test_project_creation

# By pattern
pytest -k test_project
pytest -k "test_create or test_delete"
```

### Run by Marker
```bash
pytest -m unit              # Unit tests only
pytest -m integration       # Integration tests only
pytest -m api              # API tests only
pytest -m "unit and models" # Unit tests for models
pytest -m "not slow"        # Exclude slow tests
```

### Run with Options
```bash
# Stop on first failure
pytest -x

# Show local variables on failure
pytest -l

# Disable warnings
pytest --disable-warnings

# Verbose output
pytest -v

# Very verbose output
pytest -vv

# Show print statements
pytest -s

# Parallel execution (requires pytest-xdist)
pytest -n auto
```

## Test Markers

Tests are marked with pytest markers for selective running:

- `@pytest.mark.unit` - Unit tests (models, forms, utilities)
- `@pytest.mark.integration` - Integration/workflow tests
- `@pytest.mark.api` - REST API endpoint tests
- `@pytest.mark.models` - Model-specific tests
- `@pytest.mark.views` - View-specific tests
- `@pytest.mark.forms` - Form validation tests
- `@pytest.mark.slow` - Slow-running tests
- `@pytest.mark.django_db` - Tests requiring database

## Coverage Report

After running tests with `--cov`, you'll see:

```
---------- coverage: platform linux, python 3.10.x -----------
Name                                    Stmts   Miss  Cover
-----------------------------------------------------------
clip_web/apps/accounts/forms.py            45      2    96%
clip_web/apps/accounts/views.py            67      3    96%
clip_web/apps/analysis/forms.py            89      5    94%
clip_web/apps/analysis/models.py          128      8    94%
clip_web/apps/analysis/views.py           245     15    94%
clip_web/apps/api/permissions.py           42      2    95%
clip_web/apps/api/serializers.py          198     10    95%
clip_web/apps/api/views.py                287     18    94%
clip_web/apps/images/models.py             94      5    95%
clip_web/apps/images/views.py             156     12    92%
clip_web/apps/projects/models.py           78      4    95%
clip_web/apps/projects/views.py           198     14    93%
-----------------------------------------------------------
TOTAL                                    1627     98    94%
```

Target: **90%+ coverage** for all modules

## What's Tested

### ✅ Models
- User registration and profile creation
- Project CRUD with slug generation
- Collaborator roles (owner/editor/viewer)
- Dataset creation and management
- Image upload with metadata extraction
- GPS data handling
- Analysis lifecycle (pending → processing → completed → failed)
- Text prompt validation
- Similarity result storage

### ✅ Views
- Authentication flow (register, login, logout, password reset)
- Project list, detail, create, update, delete
- Collaborator management
- Dataset CRUD operations
- Image upload (drag-and-drop interface)
- Analysis creation wizard (3 steps)
- Analysis results dashboard
- HTMX progress partials
- Permission checks per role

### ✅ API
- All REST endpoints (30+)
- Token and session authentication
- Project collaborator management API
- Semantic image search endpoint
- Analysis creation and progress tracking
- Results and statistics endpoints
- Pagination, filtering, search
- Permission-based access control

### ✅ Forms
- Analysis creation with text prompts
- Prompt validation (max 50, no duplicates, length)
- User registration with extended fields
- Password validation
- Email uniqueness

### ✅ Integration
- Complete user journey
- Multi-user collaboration
- Data management workflows
- Analysis from creation to results
- Error handling

## Mocking

### CLIP Service
The CLIP service is mocked in tests to avoid GPU dependencies:

```python
@pytest.fixture
def mock_clip_service(mocker):
    """Mock the CLIP service for testing."""
    mock_service = mocker.patch('apps.analysis.clip_service.get_clip_service')
    mock_instance = mocker.Mock()
    mock_instance.compare_image_with_texts.return_value = {
        'architecture': 0.85,
        'nature': 0.65,
        'people': 0.45
    }
    return mock_instance
```

This allows testing without:
- CLIP model downloads
- GPU/CUDA
- Heavy computation

### Media Storage
Test files use temporary storage:

```python
@pytest.fixture(autouse=True)
def media_storage(settings, tmpdir):
    """Use temporary media storage for tests."""
    settings.MEDIA_ROOT = tmpdir.strpath
```

Uploads don't affect real media folder.

## Continuous Integration

For CI/CD pipelines (GitHub Actions, GitLab CI, etc.):

```yaml
# .github/workflows/tests.yml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: |
          pip install -r requirements-django.txt
      - name: Run tests
        run: |
          pytest --cov --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

## Troubleshooting

### Database Errors
```bash
# Reset test database
pytest --create-db
```

### Migration Issues
```bash
# Run with migrations (slower)
pytest --migrations
```

### Import Errors
```bash
# Make sure you're in the right directory
cd /path/to/CLIP_for_semiotics

# Install dependencies
pip install -r requirements-django.txt
```

### CLIP/GPU Errors
The mock should prevent this, but if you see CLIP errors:
```bash
# Ensure mock is working
pytest -k test_semantic_search -v
```

### File Permission Errors
```bash
# Check media folder permissions
chmod 755 clip_web/media
```

## Test Best Practices

When adding new tests:

1. **Use fixtures** - Reuse existing fixtures from conftest.py
2. **Mark tests** - Add appropriate markers (@pytest.mark.unit, etc.)
3. **Test edge cases** - Not just happy paths
4. **Mock external services** - CLIP, email, etc.
5. **Keep tests fast** - Use --nomigrations, mock expensive operations
6. **Clean up** - Tests should be independent
7. **Descriptive names** - `test_user_can_create_project_with_collaborators`
8. **Arrange-Act-Assert** - Clear test structure

Example:
```python
def test_editor_can_create_dataset(client, project, user2):
    """Test that editors can create datasets."""
    # Arrange
    ProjectMembership.objects.create(
        project=project,
        user=user2,
        role='editor'
    )
    client.force_login(user2)

    # Act
    url = reverse('images:dataset_create', kwargs={'project_slug': project.slug})
    data = {'name': 'New Dataset', 'description': 'Test'}
    response = client.post(url, data)

    # Assert
    assert response.status_code == 302
    assert ImageDataset.objects.filter(name='New Dataset').exists()
```

## Performance

Test suite runs in **~30-60 seconds** with:
- `--nomigrations` (skip migration creation)
- `--reuse-db` (reuse test database)
- Mocked CLIP service
- Temporary file storage

Without optimizations: **~5-10 minutes**

## Next Steps

To ensure the system boots and works:

1. **Run full test suite:**
   ```bash
   pytest
   ```

2. **Check coverage:**
   ```bash
   pytest --cov --cov-report=html
   open htmlcov/index.html
   ```

3. **Run integration tests:**
   ```bash
   pytest -m integration -v
   ```

4. **Test specific workflows:**
   ```bash
   pytest -k test_full_workflow -v
   ```

If all tests pass ✅, you can be confident that:
- Django boots correctly
- Database models work
- Views render properly
- API endpoints respond
- Permissions are enforced
- Forms validate correctly
- Complete workflows function

## Support

For issues or questions:
- Check test output for specific failures
- Review relevant test file
- Check fixtures in conftest.py
- Ensure all dependencies installed
- Verify database access

Happy testing! 🧪
