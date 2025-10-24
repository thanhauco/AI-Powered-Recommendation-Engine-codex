# AI-Powered Recommendation Engine

An enterprise-ready recommendation platform that fuses a production-grade FastAPI backend with a modern HTMX/Tailwind experience. It orchestrates collaborative filtering, content-based retrieval, and learning-to-rank signals to deliver explainable, diversified results across user dashboards, admin tooling, and analytics workflows.

## What’s Inside

- **Hybrid Intelligence** – Matrix factorization (implicit ALS fallback) blended with TF-IDF content vectors, LightGBM/XGBoost rankers, and business-rule diversification. Each recommendation surfaces “why this?” explanations and supports feature-flag-controlled model rollouts.
- **Hardened Backend** – FastAPI with async SQLAlchemy 2.0, PostgreSQL 15, Redis caching, Celery workers, and structured logging. JWT auth covers access + refresh tokens, RBAC (admin/analyst/user), sticky AB test assignments, and secure settings via `pydantic-settings`.
- **ML Lifecycle** – Deterministic seed scripts (100+ items, 1k+ events), reproducible training/evaluation pipelines, MAP@K/NDCG@K reporting, artifact versioning, and online metrics exported to Prometheus/Grafana.
- **2025-Grade UI** – Server-rendered Jinja templates enhanced with HTMX + Alpine.js for micro-interactions, responsive dark/light themes, skeleton loaders, accessibility (WCAG AA), admin consoles, and analytics dashboards.
- **Ops & Deployment** – Docker Compose stack (web, worker, scheduler, Postgres, Redis, Prometheus, Grafana), Makefile helpers, single-VM deployment blueprint, feature flags, health probes, and observability hooks for tracing/metrics.

Built for technical founders and lean teams who need a ready-to-run personalization engine that they can extend, deploy, and trust.
