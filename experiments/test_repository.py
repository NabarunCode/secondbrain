# experiments/test_repository.py
#
# End-to-end check of the Phase 1B catalog: apply schema.sql, persist a
# real Asset through AssetRepository, retrieve it back, confirm it matches.
#
# data/secondbrain.db persists between runs (that's the point -- init_db()
# never touches existing rows), so re-running this with the same hardcoded
# id hits AssetAlreadyExistsError on the second and later runs. That's
# expected, not a bug: create() now reports the collision clearly instead
# of leaking a raw sqlite3.IntegrityError.
#
# Run with: uv run python experiments/test_repository.py

from datetime import datetime

from secondbrain.catalog.connection import get_connection
from secondbrain.catalog.schema import init_db
from secondbrain.catalog.asset_repository import AssetRepository, AssetAlreadyExistsError
from secondbrain.models.asset import Asset
from secondbrain.models.asset_type import AssetType
from secondbrain.models.storage_status import StorageStatus


def main():
    conn = get_connection()
    init_db(conn)
    repo = AssetRepository(conn)

    asset = Asset(
        id="01JZFQ8NK9R2QK4Q7P2M8C1YAB",
        asset_type=AssetType.PHOTO,
        storage_status=StorageStatus.DISCOVERED,
        filename="IMG001.JPG",
        mime_type="image/jpeg",
        size_bytes=14567342,
        file_modified_at=datetime.now(),
        title="Test Photo",
        tags=["vacation", "family"],
    )

    try:
        repo.create(asset)
        print(f"Created asset: {asset.id}")
    except AssetAlreadyExistsError:
        print(f"Asset {asset.id} already exists -- skipping create, reading it back instead.")

    fetched = repo.get(asset.id)
    print(f"Retrieved: {fetched.filename} | {fetched.title} | {fetched.tags} | "
          f"{fetched.asset_type} | {fetched.storage_status}")

    match = (
        fetched.id == asset.id
        and fetched.filename == asset.filename
        and set(fetched.tags) == set(asset.tags)
    )
    print(f"Round-trip match: {match}")


if __name__ == "__main__":
    main()
