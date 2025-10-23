from __future__ import annotations

import argparse
import asyncio
import csv
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Iterable

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.models import Item


@dataclass
class CatalogRow:
    sku: str
    title: str
    description: str
    categories: list[str]
    tags: list[str]
    brand: str | None
    color: str | None
    price: Decimal
    inventory_count: int


def parse_list(value: str) -> list[str]:
    return [part.strip() for part in value.split("|") if part.strip()]


def read_catalog(csv_path: Path) -> Iterable[CatalogRow]:
    with csv_path.open("r", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            yield CatalogRow(
                sku=row["sku"],
                title=row["title"],
                description=row["description"],
                categories=parse_list(row.get("categories", "")),
                tags=parse_list(row.get("tags", "")),
                brand=row.get("brand") or None,
                color=row.get("color") or None,
                price=Decimal(row.get("price", "0.00")),
                inventory_count=int(row.get("inventory_count", "0")),
            )


async def upsert_item(session: AsyncSession, payload: CatalogRow) -> None:
    existing: Item | None = await session.scalar(select(Item).where(Item.sku == payload.sku))
    if existing:
        existing.title = payload.title
        existing.description = payload.description
        existing.categories = payload.categories
        existing.tags = payload.tags
        existing.brand = payload.brand
        existing.color = payload.color
        existing.price = payload.price
        existing.inventory_count = payload.inventory_count
        metadata = dict(existing.metadata_json or {})
        metadata["source"] = "catalog_csv"
        existing.metadata_json = metadata
        existing.updated_at = datetime.now(tz=UTC)
    else:
        session.add(
            Item(
                sku=payload.sku,
                title=payload.title,
                description=payload.description,
                categories=payload.categories,
                tags=payload.tags,
                brand=payload.brand,
                color=payload.color,
                price=payload.price,
                inventory_count=payload.inventory_count,
                metadata_json={"source": "catalog_csv"},
                is_active=True,
            )
        )


async def load_catalog(csv_path: Path) -> None:
    settings = get_settings()
    engine = create_async_engine(str(settings.database_url), future=True)
    session_factory: async_sessionmaker[AsyncSession] = async_sessionmaker(bind=engine, expire_on_commit=False)

    rows = list(read_catalog(csv_path))
    if not rows:
        raise SystemExit("Catalog CSV is empty; nothing to import.")

    async with session_factory() as session:
        for row in rows:
            await upsert_item(session, row)
        await session.commit()

    await engine.dispose()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Load catalog data from CSV into the database.")
    parser.add_argument(
        "--path",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "data" / "catalog.csv",
        help="Path to catalog CSV file.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not args.path.exists():
        raise SystemExit(f"Catalog file not found: {args.path}")
    asyncio.run(load_catalog(args.path))


if __name__ == "__main__":
    main()
