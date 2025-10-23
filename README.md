# AI-Powered Recommendation Engine

- Full-stack FastAPI platform that blends collaborative, content-based, and learning-to-rank models to deliver personalized recommendations with explainability.
- Production-grade architecture: async SQLAlchemy + Alembic on PostgreSQL, Redis-backed caching and Celery workers, JWT auth with RBAC, feature flags, Prometheus + Grafana observability.
- Modern HTMX/Jinja UI styled with Tailwind v3 and Alpine.js, offering responsive dashboards, admin tooling, and analytics with accessibility and dark-mode support.
- ML workflow covers deterministic seeding, hybrid feature store, offline/online metrics, AB testing, and artifact versioning for single-VM or Docker deployments.
