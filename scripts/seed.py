from __future__ import annotations

import asyncio
import math
import random
from datetime import UTC, datetime, timedelta
from decimal import Decimal
import hashlib
from typing import Sequence

import numpy as np
from faker import Faker
from passlib.context import CryptContext
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.models import (
    ABTest,
    ABTestAssignment,
    ABTestStatus,
    ABTestVariant,
    EventLog,
    FeatureFlag,
    Interaction,
    InteractionType,
    Item,
    ItemEmbedding,
    RecommendationScore,
    User,
    UserEmbedding,
    UserRole,
)

faker = Faker()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
settings = get_settings()

RANDOM_SEED = 1337
NUM_USERS = 75
NUM_ITEMS = 120
NUM_INTERACTIONS = 1500
EMBEDDING_DIM = 32
MODEL_VERSION = "v1.0.0"


def deterministic_seed() -> None:
    """Seed all random number generators for reproducibility."""

    random.seed(RANDOM_SEED)
    np.random.seed(RANDOM_SEED)
    faker.seed_instance(RANDOM_SEED)


async def truncate_tables(session: AsyncSession) -> None:
    """Truncate tables to allow deterministic reseeding."""

    tables = [
        "event_logs",
        "feature_store_recommendation_scores",
        "feature_store_item_embeddings",
        "feature_store_user_embeddings",
        "ab_test_assignments",
        "ab_tests",
        "feature_flags",
        "interactions",
        "items",
        "users",
    ]
    for table in tables:
        await session.execute(text(f'TRUNCATE TABLE "{table}" RESTART IDENTITY CASCADE'))
    await session.commit()


def hash_password(password: str) -> str:
    """Hash a plaintext password using bcrypt."""

    return pwd_context.hash(password)


def build_users() -> list[User]:
    """Create deterministic user fixtures."""

    users: list[User] = [
        User(
            email="admin@example.com",
            full_name="Admin User",
            role=UserRole.ADMIN,
            hashed_password=hash_password("AdminPass123!"),
            feature_flags=["beta-dashboard"],
        ),
        User(
            email="analyst@example.com",
            full_name="Analyst User",
            role=UserRole.ANALYST,
            hashed_password=hash_password("AnalystPass123!"),
        ),
    ]

    for _ in range(NUM_USERS - len(users)):
        profile = faker.simple_profile()
        users.append(
            User(
                email=profile["mail"],
                full_name=profile["name"],
                role=UserRole.USER,
                hashed_password=hash_password("UserPass123!"),
                preferences={
                    "preferred_categories": random.sample(
                        ["electronics", "home", "fitness", "music", "outdoors", "fashion"],
                        k=3,
                    ),
                    "price_sensitivity": random.choice(["low", "medium", "high"]),
                },
            )
        )
    return users


def build_items() -> list[Item]:
    """Create catalog items with rich metadata."""

    categories_pool = [
        "electronics",
        "fashion",
        "home",
        "fitness",
        "music",
        "outdoors",
        "beauty",
        "gaming",
        "books",
        "photography",
    ]
    colors = ["black", "white", "red", "green", "blue", "purple", "silver", "gold"]

    items: list[Item] = []
    for idx in range(NUM_ITEMS):
        category_primary = random.choice(categories_pool)
        extra_categories_pool = [c for c in categories_pool if c != category_primary]
        tags = random.sample(
            [
                "wireless",
                "sustainable",
                "limited",
                "ergonomic",
                "smart",
                "portable",
                "premium",
                "budget",
                "eco",
                "modular",
            ],
            k=5,
        )
        price_value = Decimal(f"{random.uniform(19.99, 499.99):.2f}")
        extra_categories = random.sample(extra_categories_pool, k=2)
        items.append(
            Item(
                sku=f"SKU-{1000+idx}",
                title=faker.catch_phrase(),
                description=f"{faker.text(max_nb_chars=180)}\n\nKey benefits:\n- {faker.sentence()}\n- {faker.sentence()}",
                categories=[category_primary, *extra_categories],
                tags=tags,
                brand=random.choice(["Aurora Labs", "Nimbus Co.", "Vertex", "Pulse"]),
                color=random.choice(colors),
                price=price_value,
                inventory_count=random.randint(20, 500),
                metadata_json={
                    "material": random.choice(["aluminum", "carbon fiber", "organic cotton", "recycled plastic"]),
                    "origin_country": random.choice(["USA", "Germany", "Japan", "Sweden", "Canada"]),
                },
                release_date=faker.date_between(start_date="-2y", end_date="today"),
                rating_average=round(random.uniform(3.0, 4.9), 2),
            )
        )
    return items


def build_interactions(users: Sequence[User], items: Sequence[Item]) -> list[Interaction]:
    """Generate synthetic interaction events."""

    interactions: list[Interaction] = []
    now = datetime.now(tz=UTC)
    event_types = [
        InteractionType.VIEW,
        InteractionType.CLICK,
        InteractionType.ADD_TO_CART,
        InteractionType.PURCHASE,
        InteractionType.RATING,
    ]

    for _ in range(NUM_INTERACTIONS):
        user = random.choice(users)
        item = random.choice(items)
        event_type = random.choices(
            population=event_types,
            weights=[0.55, 0.20, 0.15, 0.07, 0.03],
            k=1,
        )[0]
        timestamp = now - timedelta(days=random.randint(0, 120), hours=random.randint(0, 23))
        weight = {
            InteractionType.VIEW: 0.2,
            InteractionType.CLICK: 0.4,
            InteractionType.ADD_TO_CART: 0.6,
            InteractionType.PURCHASE: 1.0,
            InteractionType.RATING: 0.8,
        }[event_type]
        rating = None
        if event_type == InteractionType.RATING:
            rating = round(random.uniform(3.0, 5.0), 1)

        interactions.append(
            Interaction(
                user_id=user.id,
                item_id=item.id,
                event_type=event_type,
                event_at=timestamp,
                weight=weight,
                rating=rating,
                source=random.choice(["web", "mobile", "email"]),
                metadata_json={"session_id": faker.uuid4()},
            )
        )
    return interactions


def build_feature_flags(admin_user: User) -> list[FeatureFlag]:
    """Seed feature flags for experimentation."""

    return [
        FeatureFlag(
            name="Hybrid Recommender Rollout",
            slug="hybrid-recommender",
            description="Enable new hybrid ranking model blending collaborative and content signals.",
            is_enabled=True,
            rollout_percentage=60,
            owner_id=admin_user.id,
            rules={"segment": "power_users"},
        ),
        FeatureFlag(
            name="Explainability Modal",
            slug="explainability-modal",
            description="Expose 'Why this recommendation?' modal to users.",
            is_enabled=False,
            rollout_percentage=20,
            owner_id=admin_user.id,
        ),
    ]


def build_ab_tests(admin_user: User) -> list[ABTest]:
    """Create sample AB tests."""

    return [
        ABTest(
            name="Ranking Strategy Experiment",
            slug="ranking-strategy-experiment",
            description="Compare baseline collaborative filter vs. hybrid ranker.",
            status=ABTestStatus.RUNNING,
            hypothesis="Hybrid ranker increases CTR by 8% for engaged users.",
            primary_metric="ctr",
            secondary_metrics=["conversion_rate", "avg_order_value"],
            variant_a_config={"model_version": "cf-v0.9"},
            variant_b_config={"model_version": "hybrid-v1.0"},
            start_at=datetime.now(tz=UTC) - timedelta(days=7),
            traffic_percentage=50,
            created_by_id=admin_user.id,
        )
    ]


def build_ab_test_assignments(
    ab_tests: list[ABTest],
    users: Sequence[User],
) -> list[ABTestAssignment]:
    """Assign users to AB test variants deterministically."""

    assignments: list[ABTestAssignment] = []
    for ab_test in ab_tests:
        for user in users:
            digest = hashlib.sha256(f"{ab_test.slug}:{user.email}".encode("utf-8")).hexdigest()
            bucket = int(digest, 16) % 100
            if bucket > ab_test.traffic_percentage:
                continue

            variant = ABTestVariant.TREATMENT if bucket % 2 == 0 else ABTestVariant.CONTROL
            assignments.append(
                ABTestAssignment(
                    ab_test_id=ab_test.id,
                    user_id=user.id,
                    variant=variant,
                    assigned_at=datetime.now(tz=UTC) - timedelta(days=random.randint(1, 7)),
                    metadata_json={"bucket": bucket},
                )
            )
    return assignments


def build_embeddings(
    users: Sequence[User],
    items: Sequence[Item],
) -> tuple[list[UserEmbedding], list[ItemEmbedding], list[RecommendationScore]]:
    """Create deterministic embeddings and recommendation scores."""

    user_embeddings: list[UserEmbedding] = []
    item_embeddings: list[ItemEmbedding] = []
    rec_scores: list[RecommendationScore] = []

    now = datetime.now(tz=UTC)
    for user in users:
        vector = np.random.rand(EMBEDDING_DIM)
        user_embeddings.append(
            UserEmbedding(
                user_id=user.id,
                model_version=MODEL_VERSION,
                embedding=vector.tolist(),
                embedding_dim=EMBEDDING_DIM,
                metadata_json={"generator": "seed-script"},
                computed_at=now,
            )
        )

    for item in items:
        vector = np.random.rand(EMBEDDING_DIM)
        item_embeddings.append(
            ItemEmbedding(
                item_id=item.id,
                model_version=MODEL_VERSION,
                embedding=vector.tolist(),
                embedding_dim=EMBEDDING_DIM,
                metadata_json={"generator": "seed-script"},
                computed_at=now,
            )
        )

    for user in users:
        top_items = random.sample(items, k=10)
        for rank, item in enumerate(top_items, start=1):
            rec_scores.append(
                RecommendationScore(
                    user_id=user.id,
                    item_id=item.id,
                    model_version=MODEL_VERSION,
                    score=float(math.exp(-rank / 5)),
                    rank=rank,
                    explanation={"collaborative": round(random.uniform(0.4, 0.7), 3), "content": round(random.uniform(0.3, 0.6), 3)},
                    computed_at=now,
                )
            )

    return user_embeddings, item_embeddings, rec_scores


def build_event_logs(
    users: Sequence[User],
    ab_tests: Sequence[ABTest],
) -> list[EventLog]:
    """Generate operational event logs."""

    events: list[EventLog] = []
    now = datetime.now(tz=UTC)
    ab_test_id = ab_tests[0].id if ab_tests else None

    for user in users[:20]:
        events.append(
            EventLog(
                event_type="user.login",
                user_id=user.id,
                ab_test_id=ab_test_id,
                payload={"auth_method": "password"},
                metadata_json={"ip": faker.ipv4_public()},
                occurred_at=now - timedelta(days=random.randint(0, 5)),
            )
        )

    events.append(
        EventLog(
            event_type="ml.training.completed",
            user_id=None,
            ab_test_id=ab_test_id,
            payload={"model_version": MODEL_VERSION, "duration_seconds": 284},
            metadata_json={"status": "success"},
            occurred_at=now - timedelta(days=1),
        )
    )

    return events


async def seed() -> None:
    """Main asynchronous seeding entrypoint."""

    deterministic_seed()
    engine: AsyncEngine = create_async_engine(str(settings.database_url), future=True)
    SessionLocal: async_sessionmaker[AsyncSession] = async_sessionmaker(bind=engine, expire_on_commit=False)

    async with SessionLocal() as session:
        await truncate_tables(session)

    async with SessionLocal() as session:
        users = build_users()
        session.add_all(users)
        await session.flush()

        items = build_items()
        session.add_all(items)
        await session.flush()

        interactions = build_interactions(users, items)
        session.add_all(interactions)

        admin_user = users[0]
        feature_flags = build_feature_flags(admin_user)
        session.add_all(feature_flags)

        ab_tests = build_ab_tests(admin_user)
        session.add_all(ab_tests)
        await session.flush()

        assignments = build_ab_test_assignments(ab_tests, users)
        session.add_all(assignments)

        user_embeddings, item_embeddings, rec_scores = build_embeddings(users, items)
        session.add_all(user_embeddings)
        session.add_all(item_embeddings)
        session.add_all(rec_scores)

        event_logs = build_event_logs(users, ab_tests)
        session.add_all(event_logs)

        await session.commit()

    await engine.dispose()


def main() -> None:
    """CLI entrypoint."""

    asyncio.run(seed())


if __name__ == "__main__":
    main()
