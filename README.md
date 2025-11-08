# CLIP for Humanists

A Django web application for analyzing images using OpenAI's CLIP (Contrastive Language-Image Pre-training) model. Designed for humanities researchers to perform semantic analysis of visual materials without requiring technical expertise.

## 🌟 Features

- **Project Management**: Organize your research with projects and datasets
- **Image Upload**: Bulk upload and manage image collections
- **CLIP Analysis**: Compare images against custom text prompts
- **Rich Visualizations**:
  - Similarity heatmaps
  - Correlation matrices
  - Image grids sorted by scores
  - Interactive maps (for geotagged images)
- **REST API**: Full programmatic access to all features
- **Async Processing**: Background task processing with Celery
- **User Management**: Multi-user support with permissions
- **Export**: Download results in multiple formats

## 📋 Requirements

- Python 3.11+
- PostgreSQL 14+ (recommended) or SQLite (development)
- Redis (for Celery task queue)
- ~4GB RAM (for CLIP model)

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/CLIP_for_semiotics.git
cd CLIP_for_semiotics
```

### 2. Set Up Virtual Environment

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 3. Install Dependencies

```bash
# Install Django app dependencies
pip install -r clip_web/requirements-django.txt

# Optional: Install CLIP dependencies (for actual analysis)
pip install -r requirements.txt
```

### 4. Configure Environment

```bash
cp clip_web/.env.example clip_web/.env
# Edit clip_web/.env with your settings
```

### 5. Initialize Database

```bash
cd clip_web
python manage.py migrate
python manage.py createsuperuser
```

### 6. Run Development Server

```bash
python manage.py runserver
```

Visit http://localhost:8000 to access the application.

## 📚 Documentation

All documentation is in the `docs/` directory:

- [**Project Status**](docs/PROJECT_STATUS.md) - Current development status and roadmap
- [**Running Locally**](docs/RUNNING_LOCALLY.md) - Detailed local development guide
- [**Testing**](docs/TESTING.md) - Running and writing tests
- [**Visualization API**](docs/VISUALIZATION_API_DOCS.md) - REST API reference
- [**Django Migration Workplan**](docs/DJANGO_MIGRATION_WORKPLAN.md) - Migration from notebooks

## 🔧 Development

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest clip_web/tests/unit/test_models.py

# Run with coverage
pytest --cov=clip_web
```

### Running Celery Worker (for async tasks)

```bash
# Terminal 1: Start Redis
redis-server

# Terminal 2: Start Celery worker
cd clip_web
celery -A config worker -l info

# Terminal 3: Start Celery beat (for scheduled tasks)
celery -A config beat -l info
```

### Code Style

```bash
# Format code
black clip_web/

# Check linting
flake8 clip_web/

# Type checking
mypy clip_web/
```

## 📖 Usage Examples

### Basic Analysis (Django ORM)

```python
python examples/basic_analysis.py
```

### API Usage (REST API)

```bash
# Create an analysis via API
curl -X POST http://localhost:8000/api/v1/analyses/ \
  -H "Authorization: Token YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "dataset": 1,
    "name": "My Analysis",
    "text_prompts": ["happy", "sad", "neutral"]
  }'

# Generate visualizations
curl -X POST http://localhost:8000/api/v1/visualizations/generate_default/ \
  -H "Authorization: Token YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"analysis_id": 1}'
```

See [API Documentation](docs/VISUALIZATION_API_DOCS.md) for full reference.

## 🗂️ Project Structure

```
CLIP_for_semiotics/
├── clip_web/              # Django application
│   ├── apps/              # Django apps
│   │   ├── accounts/      # User management
│   │   ├── analysis/      # CLIP analysis
│   │   ├── api/           # REST API
│   │   ├── images/        # Image management
│   │   ├── projects/      # Project organization
│   │   └── visualizations/# Visualization generation
│   ├── config/            # Django settings
│   ├── templates/         # HTML templates
│   ├── static/            # Static files
│   └── tests/             # Test suite
├── docs/                  # Documentation
├── examples/              # Usage examples
├── img/                   # Example images
└── src/                   # Original notebook code (legacy)
```

## 🧪 Testing

**Test Coverage**: 147 tests, 136 passing (93%)

- **Models**: 28/28 passing (100%)
- **Forms**: 11/11 passing (100%)
- **Views**: 35/35 passing (100%)
- **API**: 26/28 passing (93%)
- **Visualizations**: 33/34 passing (97%)

Run the test suite:

```bash
pytest
```

See [docs/TEST_RESULTS.md](docs/TEST_RESULTS.md) for detailed results.

## 🎨 Visualization Types

### 1. Similarity Heatmap
Shows similarity scores between images (rows) and text prompts (columns).

### 2. Correlation Matrix
Displays how different text prompts correlate across your image set.

### 3. Image Grid
Displays images sorted by similarity scores for visual inspection.

### 4. Interactive Maps (Coming Soon)
Visualize image locations on maps with Folium integration.

## 🔐 Authentication

The application supports multiple authentication methods:

- **Session Authentication**: For web UI
- **Token Authentication**: For API access
- **API Keys**: For programmatic access

Get your API token:

```bash
python manage.py drf_create_token <username>
```

## 📊 Database Schema

Key models:

- **User**: Django users with profiles
- **Project**: Top-level organization
- **ImageDataset**: Collections of images
- **Image**: Individual image with metadata
- **Analysis**: CLIP analysis configuration
- **TextPrompt**: Text prompts for comparison
- **SimilarityResult**: CLIP similarity scores
- **Visualization**: Generated visualizations

See [Django Models](clip_web/apps/) for full schema.

## 🚢 Deployment

### Production Checklist

- [ ] Set `DEBUG=False` in settings
- [ ] Configure PostgreSQL database
- [ ] Set up Redis for Celery
- [ ] Configure static files (collectstatic)
- [ ] Set up proper SECRET_KEY
- [ ] Configure allowed hosts
- [ ] Set up reverse proxy (nginx)
- [ ] Configure SSL/TLS
- [ ] Set up monitoring
- [ ] Configure backups

See [deployment guide](docs/RUNNING_LOCALLY.md#production-deployment) for details.

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Status

**Current Phase**: Phase 3 - Visualization Layer (75% complete)
**Overall Progress**: 52% complete

See [docs/PROJECT_STATUS.md](docs/PROJECT_STATUS.md) for the full roadmap.

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Built on [OpenAI's CLIP](https://github.com/openai/CLIP)
- Django web framework
- Bootstrap 5 for UI
- HTMX for dynamic updates
- Matplotlib, Seaborn, Folium for visualizations

## 📧 Contact

For questions, issues, or suggestions:

- **Issues**: [GitHub Issues](https://github.com/yourusername/CLIP_for_semiotics/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/CLIP_for_semiotics/discussions)

## 🗺️ Roadmap

- [x] Phase 1: Django Foundation (100%)
- [x] Phase 2: Core Processing (100%)
- [x] Phase 3.1-3.3: Basic Visualizations (75%)
- [ ] Phase 3.4-3.5: Advanced Visualizations (25%)
- [ ] Phase 4: User Features (0%)
- [ ] Phase 5: CLIP Integration (20%)
- [ ] Phase 6: Deployment (0%)

See [full roadmap](docs/PROJECT_STATUS.md) for details.

---

**Made with ❤️ for humanities researchers**
