"""Initial schema"""

from __future__ import annotations

from datetime import datetime

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "20250101_0001"
down_revision = None
branch_labels = None
depends_on = None

userrole_enum = sa.Enum("admin", "analyst", "user", name="userrole")
interactiontype_enum = sa.Enum(
    "view",
    "click",
    "add_to_cart",
    "purchase",
    "rating",
    name="interactiontype",
)
abteststatus_enum = sa.Enum("draft", "running", "paused", "completed", "cancelled", name="abteststatus")
abtestvariant_enum = sa.Enum("control", "treatment", "holdout", name="abtestvariant")


def upgrade() -> None:
    bind = op.get_bind()
    userrole_enum.create(bind, checkfirst=True)
    interactiontype_enum.create(bind, checkfirst=True)
    abteststatus_enum.create(bind, checkfirst=True)
    abtestvariant_enum.create(bind, checkfirst=True)

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=120), nullable=True),
        sa.Column("role", userrole_enum, nullable=False, server_default="user"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("preferences", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("feature_flags", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("last_login_at", sa.String(length=64), nullable=True),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=False)

    op.create_table(
        "items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("sku", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("categories", postgresql.ARRAY(sa.String(length=64)), nullable=False, server_default=sa.text("'{}'::text[]")),
        sa.Column("tags", postgresql.ARRAY(sa.String(length=64)), nullable=False, server_default=sa.text("'{}'::text[]")),
        sa.Column("brand", sa.String(length=120), nullable=True),
        sa.Column("color", sa.String(length=64), nullable=True),
        sa.Column("price", sa.Numeric(precision=10, scale=2), nullable=False, server_default=sa.text("0")),
        sa.Column("inventory_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("release_date", sa.Date(), nullable=True),
        sa.Column("rating_average", sa.Float(), nullable=True),
        sa.UniqueConstraint("sku", name="uq_items_sku"),
    )
    op.create_index(
        "ix_items_title_trgm",
        "items",
        ["title"],
        unique=False,
        postgresql_using="gin",
        postgresql_ops={"title": "gin_trgm_ops"},
    )
    op.create_index(
        "ix_items_description_trgm",
        "items",
        ["description"],
        unique=False,
        postgresql_using="gin",
        postgresql_ops={"description": "gin_trgm_ops"},
    )

    op.create_table(
        "ab_tests",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=255), nullable=False),
        sa.Column("description", sa.String(length=1024), nullable=True),
        sa.Column("status", abteststatus_enum, nullable=False, server_default="draft"),
        sa.Column("hypothesis", sa.String(length=1024), nullable=True),
        sa.Column("primary_metric", sa.String(length=128), nullable=False, server_default="ctr"),
        sa.Column("secondary_metrics", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("variant_a_config", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("variant_b_config", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("start_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("end_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("traffic_percentage", sa.Integer(), nullable=False, server_default=sa.text("50")),
        sa.Column("created_by_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], name=op.f("fk_ab_tests_created_by_id_users")),
        sa.UniqueConstraint("slug", name="uq_ab_tests_slug"),
    )

    op.create_table(
        "feature_flags",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=255), nullable=False),
        sa.Column("description", sa.String(length=1024), nullable=True),
        sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("rollout_percentage", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("rules", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], name=op.f("fk_feature_flags_owner_id_users"), ondelete="SET NULL"),
        sa.UniqueConstraint("slug", name="uq_feature_flags_slug"),
    )

    op.create_table(
        "feature_store_item_embeddings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("item_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("model_version", sa.String(length=64), nullable=False),
        sa.Column("embedding", postgresql.ARRAY(sa.Float()), nullable=False),
        sa.Column("embedding_dim", sa.Integer(), nullable=False),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("computed_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["item_id"], ["items.id"], name=op.f("fk_feature_store_item_embeddings_item_id_items"), ondelete="CASCADE"),
    )
    op.create_index(
        "ix_feature_store_item_embeddings_item_model",
        "feature_store_item_embeddings",
        ["item_id", "model_version"],
        unique=True,
    )

    op.create_table(
        "feature_store_user_embeddings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("model_version", sa.String(length=64), nullable=False),
        sa.Column("embedding", postgresql.ARRAY(sa.Float()), nullable=False),
        sa.Column("embedding_dim", sa.Integer(), nullable=False),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("computed_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_feature_store_user_embeddings_user_id_users"), ondelete="CASCADE"),
    )
    op.create_index(
        "ix_feature_store_user_embeddings_user_model",
        "feature_store_user_embeddings",
        ["user_id", "model_version"],
        unique=True,
    )

    op.create_table(
        "interactions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("item_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("event_type", interactiontype_enum, nullable=False),
        sa.Column("event_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("weight", sa.Float(), nullable=False, server_default=sa.text("1")),
        sa.Column("rating", sa.Float(), nullable=True),
        sa.Column("source", sa.String(length=64), nullable=False, server_default="web"),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.CheckConstraint("weight >= 0", name="ck_interactions_weight_non_negative"),
        sa.ForeignKeyConstraint(["item_id"], ["items.id"], name=op.f("fk_interactions_item_id_items"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_interactions_user_id_users"), ondelete="CASCADE"),
    )
    op.create_index(
        "ix_interactions_user_item_event",
        "interactions",
        ["user_id", "item_id", "event_type"],
        unique=False,
    )

    op.create_table(
        "feature_store_recommendation_scores",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("item_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("model_version", sa.String(length=64), nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("rank", sa.Integer(), nullable=False),
        sa.Column("explanation", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("computed_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["item_id"], ["items.id"], name=op.f("fk_feature_store_recommendation_scores_item_id_items"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_feature_store_recommendation_scores_user_id_users"), ondelete="CASCADE"),
    )
    op.create_index(
        "ix_feature_store_recommendation_scores_user_item_version",
        "feature_store_recommendation_scores",
        ["user_id", "item_id", "model_version"],
        unique=True,
    )

    op.create_table(
        "ab_test_assignments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("ab_test_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("variant", abtestvariant_enum, nullable=False, server_default="control"),
        sa.Column("assigned_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.ForeignKeyConstraint(["ab_test_id"], ["ab_tests.id"], name=op.f("fk_ab_test_assignments_ab_test_id_ab_tests"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_ab_test_assignments_user_id_users"), ondelete="CASCADE"),
        sa.UniqueConstraint("ab_test_id", "user_id", name="uq_ab_test_assignments_test_user"),
    )
    op.create_index(
        "ix_ab_test_assignments_user_variant",
        "ab_test_assignments",
        ["user_id", "variant"],
        unique=False,
    )

    op.create_table(
        "event_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("event_type", sa.String(length=128), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("ab_test_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["ab_test_id"], ["ab_tests.id"], name=op.f("fk_event_logs_ab_test_id_ab_tests"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_event_logs_user_id_users"), ondelete="SET NULL"),
    )
    op.create_index("ix_event_logs_type_created", "event_logs", ["event_type", "created_at"], unique=False)
    op.create_index("ix_event_logs_user_created", "event_logs", ["user_id", "created_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_event_logs_user_created", table_name="event_logs")
    op.drop_index("ix_event_logs_type_created", table_name="event_logs")
    op.drop_table("event_logs")

    op.drop_index("ix_ab_test_assignments_user_variant", table_name="ab_test_assignments")
    op.drop_table("ab_test_assignments")

    op.drop_index(
        "ix_feature_store_recommendation_scores_user_item_version",
        table_name="feature_store_recommendation_scores",
    )
    op.drop_table("feature_store_recommendation_scores")

    op.drop_index("ix_interactions_user_item_event", table_name="interactions")
    op.drop_table("interactions")

    op.drop_index("ix_feature_store_user_embeddings_user_model", table_name="feature_store_user_embeddings")
    op.drop_table("feature_store_user_embeddings")

    op.drop_index("ix_feature_store_item_embeddings_item_model", table_name="feature_store_item_embeddings")
    op.drop_table("feature_store_item_embeddings")

    op.drop_table("feature_flags")

    op.drop_table("ab_tests")

    op.drop_index("ix_items_description_trgm", table_name="items")
    op.drop_index("ix_items_title_trgm", table_name="items")
    op.drop_table("items")

    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")

    abtestvariant_enum.drop(op.get_bind(), checkfirst=True)
    abteststatus_enum.drop(op.get_bind(), checkfirst=True)
    interactiontype_enum.drop(op.get_bind(), checkfirst=True)
    userrole_enum.drop(op.get_bind(), checkfirst=True)
