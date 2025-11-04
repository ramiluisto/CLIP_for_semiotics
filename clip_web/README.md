# CLIP for Humanists - Django Web Application

A Django-based web application for visual semiotical analysis using CLIP (Contrastive Language-Image Pre-training). This is a production-ready migration from the original Google Colab notebook.

## Overview

CLIP for Humanists helps researchers analyze images by:
- Comparing images with custom keywords/phrases using CLIP
- Extracting and visualizing GPS data from images
- Creating various analytical visualizations
- Enabling multi-user collaboration on research projects
- Providing persistent storage and project management

## Project Structure

```
clip_web/
├── config/                     # Django configuration
│   ├── settings/              # Environment-specific settings
│   │   ├── base.py
│   │   ├── development.py
│   │   ├── production.py
│   │   └── test.py
│   ├── urls.py
│   ├── wsgi.py
│   ├── asgi.py
│   └── celery.py
├── apps/                       # Django applications
│   ├── accounts/              # User management
│   ├── projects/              # Project management
│   ├── images/                # Image handling & metadata
│   ├── analysis/              # CLIP analysis engine
│   ├── visualizations/        # Chart & map generation
│   └── api/                   # REST API
├── templates/                  # HTML templates
├── static/                     # Static files (CSS, JS)
├── media/                      # User uploads & generated files
├── docker/                     # Docker configuration
├── requirements/               # Python dependencies
└── manage.py
```

## Features

### Phase 1 (Completed)
- ✅ Django project structure
- ✅ Database models for all entities
- ✅ CLIP service integration
- ✅ GPS data extraction
- ✅ Celery async processing
- ✅ Docker configuration
- ✅ User authentication system
- ✅ Project and dataset management
- ✅ Analysis job processing
- ✅ Basic visualizations (heatmaps, correlation matrices, GPS maps)
- ✅ Export functionality (JSON, CSV, ZIP)

### Phase 2-6 (Planned)
- Web interface (templates & views)
- REST API endpoints
- Advanced visualizations
- Real-time progress updates
- Collaboration features
- API documentation
- Comprehensive testing
- Production deployment

## Installation

### Prerequisites

- Python 3.10+
- PostgreSQL 14+
- Redis 7+
- Git

### Development Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/ramiluisto/CLIP_for_semiotics.git
   cd CLIP_for_semiotics/clip_web
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements/development.txt
   ```

4. **Create environment file:**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Run migrations:**
   ```bash
   python manage.py migrate
   ```

6. **Create superuser:**
   ```bash
   python manage.py createsuperuser
   ```

7. **Run development server:**
   ```bash
   python manage.py runserver
   ```

8. **In another terminal, start Celery worker:**
   ```bash
   celery -A config worker -l info
   ```

9. **In another terminal, start Celery beat (for periodic tasks):**
   ```bash
   celery -A config beat -l info
   ```

### Docker Setup

1. **Build and run with Docker Compose:**
   ```bash
   cd docker
   docker-compose up --build
   ```

2. **Run migrations:**
   ```bash
   docker-compose exec web python manage.py migrate
   ```

3. **Create superuser:**
   ```bash
   docker-compose exec web python manage.py createsuperuser
   ```

The application will be available at http://localhost

## Configuration

### Environment Variables

Key environment variables (see `.env.example` for full list):

- `DJANGO_ENVIRONMENT`: `development`, `production`, or `test`
- `SECRET_KEY`: Django secret key
- `DB_NAME`, `DB_USER`, `DB_PASSWORD`: PostgreSQL credentials
- `CELERY_BROKER_URL`: Redis URL for Celery
- `CLIP_MODEL_NAME`: CLIP model to use (default: openai/clip-vit-base-patch32)
- `CLIP_DEVICE`: `auto`, `cuda`, or `cpu`
- `MAX_IMAGES_PER_ANALYSIS`: Maximum images per analysis job

### Database

**PostgreSQL (recommended for production):**
```bash
createdb clip_humanists
```

**SQLite (development only):**
Set `USE_SQLITE=True` in `.env`

## Usage

### Creating an Analysis (Programmatically)

```python
from apps.projects.models import Project
from apps.images.models import ImageDataset, Image
from apps.analysis.models import Analysis, TextPrompt
from apps.analysis.tasks import process_analysis_job

# Create a project
project = Project.objects.create(
    owner=user,
    name="My Research Project",
    description="Analyzing urban signage"
)

# Create a dataset
dataset = ImageDataset.objects.create(
    project=project,
    name="Urban Signs",
    created_by=user
)

# Upload images (in real app, handled by views)
# ... image upload logic ...

# Create analysis
analysis = Analysis.objects.create(
    project=project,
    dataset=dataset,
    name="Sign Analysis",
    created_by=user
)

# Add text prompts
TextPrompt.objects.create(analysis=analysis, text="warning", order=0)
TextPrompt.objects.create(analysis=analysis, text="friendly", order=1)
TextPrompt.objects.create(analysis=analysis, text="official", order=2)

# Start processing
process_analysis_job.delay(analysis.id)
```

### Admin Interface

Access the Django admin at http://localhost:8000/admin/

Features:
- User management
- Project administration
- Analysis monitoring
- Result inspection

## Architecture

### Technology Stack

- **Backend**: Django 4.2+
- **Database**: PostgreSQL 14+
- **Cache/Queue**: Redis 7+
- **Task Queue**: Celery 5.3+
- **ML/AI**: PyTorch + Transformers (CLIP)
- **Web Server**: Gunicorn + Nginx
- **Containerization**: Docker + Docker Compose

### Key Components

1. **CLIP Service** (`apps/analysis/clip_service.py`):
   - Singleton pattern for efficient model loading
   - Batch processing support
   - GPU/CPU automatic detection

2. **GPS Service** (`apps/images/gps_service.py`):
   - EXIF metadata extraction
   - Coordinate normalization
   - Distance calculations

3. **Celery Tasks** (`apps/analysis/tasks.py`):
   - Asynchronous CLIP processing
   - Progress tracking
   - Error handling and retries

4. **Visualizations** (`apps/visualizations/generators.py`):
   - Matplotlib-based charts
   - Folium interactive maps
   - Export to multiple formats

## Development

### Running Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=apps --cov-report=html

# Specific app
pytest apps/analysis/tests/
```

### Code Quality

```bash
# Format code
black .
isort .

# Lint
flake8
pylint apps/
```

### Database Migrations

```bash
# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Show migrations
python manage.py showmigrations
```

### Celery Monitoring

```bash
# Monitor Celery tasks
celery -A config inspect active
celery -A config inspect stats

# Purge all tasks
celery -A config purge
```

## API Documentation

API documentation will be available at:
- Swagger UI: http://localhost:8000/api/docs/
- ReDoc: http://localhost:8000/api/redoc/
- OpenAPI Schema: http://localhost:8000/api/schema/

(To be implemented in Phase 2)

## Deployment

### Production Checklist

- [ ] Set `DEBUG=False`
- [ ] Configure proper `SECRET_KEY`
- [ ] Set `ALLOWED_HOSTS`
- [ ] Configure PostgreSQL
- [ ] Set up Redis
- [ ] Configure email backend
- [ ] Set up static file serving
- [ ] Configure HTTPS/SSL
- [ ] Set up monitoring (Sentry)
- [ ] Configure backups
- [ ] Set up log aggregation

### Docker Production Deployment

```bash
# Build production image
docker-compose -f docker/docker-compose.yml build

# Run in production mode
DJANGO_ENVIRONMENT=production docker-compose up -d

# Collect static files
docker-compose exec web python manage.py collectstatic --noinput

# Run migrations
docker-compose exec web python manage.py migrate
```

## Performance

### Optimization Tips

1. **CLIP Model Caching**: Model is loaded once per worker
2. **Database Indexing**: Key fields are indexed
3. **Query Optimization**: Use `select_related` and `prefetch_related`
4. **Redis Caching**: Results and sessions cached
5. **Celery Concurrency**: Adjust based on available resources

### Scaling

- **Horizontal**: Add more Celery workers
- **Vertical**: Increase worker concurrency
- **Database**: Connection pooling with PgBouncer
- **GPU**: Use GPU-enabled workers for CLIP processing

## Troubleshooting

### Common Issues

**1. CLIP model not loading:**
```bash
# Check PyTorch installation
python -c "import torch; print(torch.__version__)"

# Check CUDA availability
python -c "import torch; print(torch.cuda.is_available())"
```

**2. Celery tasks not running:**
```bash
# Check Redis connection
redis-cli ping

# Check Celery workers
celery -A config inspect active
```

**3. Database connection errors:**
```bash
# Test PostgreSQL connection
psql -h localhost -U postgres -d clip_humanists
```

### Logs

- **Django**: `logs/django.log`
- **Celery**: Check Celery worker output
- **Nginx**: `/var/log/nginx/error.log`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## Acknowledgments

- OpenAI for the CLIP model
- Original CLIP for Humanists Colab notebook
- Django and Python communities

## Support

For issues and questions:
- GitHub Issues: https://github.com/ramiluisto/CLIP_for_semiotics/issues
- Documentation: See DJANGO_MIGRATION_WORKPLAN.md

## Roadmap

See `DJANGO_MIGRATION_WORKPLAN.md` for detailed implementation roadmap.

**Current Status**: Phase 1 Complete (Foundation)
**Next**: Phase 2 - Core Processing Web Interface
