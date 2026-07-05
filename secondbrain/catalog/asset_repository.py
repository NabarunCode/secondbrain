# secondbrain/catalog/asset_repository.py
#
# The only code allowed to touch SQL for assets (see decisions.md).
# Full Phase 1B surface: create, get, transition_status, add_tags, get_tags,
# get_by_sha256_verified. See docs/phase1b_catalog_architecture.md §5.

import json
import sqlite3
from pathlib import Path

from secondbrain.models.asset import Asset
from secondbrain.models.asset_type import AssetType
from secondbrain.models.storage_status import StorageStatus


class AssetAlreadyExistsError(Exception):
    """Raised by create() when an asset with this id is already in the catalog."""


class AssetNotFoundError(Exception):
    """Raised when an operation targets an asset id that isn't in the catalog."""


class AssetRepository:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def create(self, asset: Asset) -> None:
        try:
            self.conn.execute(
                """
                INSERT INTO assets (
                    id, asset_type, storage_status, failure_stage, duplicate_of,
                    filename, local_path, title, description, bucket_name, object_key,
                    mime_type, size_bytes, sha256, file_modified_at, original_date,
                    metadata_json, thumbnail_path, embedding_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    asset.id, asset.asset_type.value, asset.storage_status.value,
                    asset.failure_stage, asset.duplicate_of,
                    asset.filename, str(asset.local_path) if asset.local_path else None,
                    asset.title, asset.description, asset.bucket_name, asset.object_key,
                    asset.mime_type, asset.size_bytes, asset.sha256,
                    asset.file_modified_at.isoformat(),
                    asset.original_date.isoformat() if asset.original_date else None,
                    json.dumps(asset.metadata) if asset.metadata else None,
                    asset.thumbnail_path, asset.embedding_id,
                ),
            )
        except sqlite3.IntegrityError as e:
            if "UNIQUE constraint failed: assets.id" in str(e):
                raise AssetAlreadyExistsError(
                    f"Asset {asset.id} already exists in the catalog."
                ) from e
            raise  # some other constraint (a CHECK, NOT NULL, etc.) -- don't hide it
        if asset.tags:
            self.conn.executemany(
                "INSERT INTO asset_tags (asset_id, tag) VALUES (?, ?)",
                [(asset.id, tag) for tag in asset.tags],
            )
        self.conn.commit()

    def transition_status(
        self, asset_id: str, to_status: StorageStatus, detail: str | None = None
    ) -> None:
        row = self.conn.execute(
            "SELECT storage_status FROM assets WHERE id = ?", (asset_id,)
        ).fetchone()
        if row is None:
            raise AssetNotFoundError(f"Asset {asset_id} not found in the catalog.")
        from_status = row["storage_status"]

        # Both statements share one implicit transaction (sqlite3's default
        # behavior: DML opens it, nothing commits until conn.commit() below)
        # -- the status update and its audit-trail row land together or not
        # at all, same pattern as create()'s asset+tags insert.
        self.conn.execute(
            """
            UPDATE assets
            SET storage_status = ?, updated_at = strftime('%Y-%m-%dT%H:%M:%fZ','now')
            WHERE id = ?
            """,
            (to_status.value, asset_id),
        )
        self.conn.execute(
            """
            INSERT INTO asset_events (asset_id, from_status, to_status, detail)
            VALUES (?, ?, ?, ?)
            """,
            (asset_id, from_status, to_status.value, detail),
        )
        self.conn.commit()

    def get(self, asset_id: str) -> Asset | None:
        row = self.conn.execute(
            "SELECT * FROM assets WHERE id = ?", (asset_id,)
        ).fetchone()
        if row is None:
            return None
        return self._asset_from_row(row)

    def get_by_sha256_verified(self, sha256: str) -> Asset | None:
        """
        The dedup lookup: a file only counts as a duplicate if its hash
        matches an asset that's already VERIFIED (see README "Duplicate-safe").
        Exercises the partial unique index idx_assets_sha256_verified.
        """
        row = self.conn.execute(
            "SELECT * FROM assets WHERE sha256 = ? AND storage_status = 'verified'",
            (sha256,),
        ).fetchone()
        if row is None:
            return None
        return self._asset_from_row(row)

    def get_by_local_path(self, local_path: Path) -> Asset | None:
        """
        TODO (Phase 2 Discovery, docs/phase2_ingestion_architecture.md §5):
        Same shape as get_by_sha256_verified() just above -- one SELECT,
        return None if nothing matches, otherwise self._asset_from_row(row).

        The WHERE clause you need: local_path = ? AND storage_status != 'failed'
        (matches the partial index from schema.sql -- != 'failed' rather than
        = 'discovered', so a file mid-pipeline is still caught; only a
        previously FAILED attempt at this path allows a fresh row).
        """
        
        row = self.conn.execute(
        "SELECT * from assets WHERE local_path = ? AND storage_status != 'failed'", (str(local_path),)
        ).fetchone()

        if row is None:
            return None
        return self._asset_from_row(row)


    def add_tags(self, asset_id: str, tags: list[str]) -> None:
        exists = self.conn.execute(
            "SELECT 1 FROM assets WHERE id = ?", (asset_id,)
        ).fetchone()
        if exists is None:
            raise AssetNotFoundError(f"Asset {asset_id} not found in the catalog.")

        # OR IGNORE: tags are a set, not a log -- adding one that's already
        # there is a no-op, not an error (unlike create()'s duplicate id).
        self.conn.executemany(
            "INSERT OR IGNORE INTO asset_tags (asset_id, tag) VALUES (?, ?)",
            [(asset_id, tag) for tag in tags],
        )
        self.conn.commit()

    def get_tags(self, asset_id: str) -> list[str]:
        return [
            r[0] for r in self.conn.execute(
                "SELECT tag FROM asset_tags WHERE asset_id = ?", (asset_id,)
            ).fetchall()
        ]

    def _asset_from_row(self, row: sqlite3.Row) -> Asset:
        tags = [
            r[0] for r in self.conn.execute(
                "SELECT tag FROM asset_tags WHERE asset_id = ?", (row["id"],)
            ).fetchall()
        ]

        return Asset(
            id=row["id"],
            asset_type=AssetType(row["asset_type"]),
            storage_status=StorageStatus(row["storage_status"]),
            failure_stage=row["failure_stage"],
            duplicate_of=row["duplicate_of"],
            filename=row["filename"],
            local_path=row["local_path"],
            title=row["title"],
            description=row["description"],
            tags=tags,
            bucket_name=row["bucket_name"],
            object_key=row["object_key"],
            mime_type=row["mime_type"],
            size_bytes=row["size_bytes"],
            sha256=row["sha256"],
            file_modified_at=row["file_modified_at"],
            original_date=row["original_date"],
            metadata=json.loads(row["metadata_json"]) if row["metadata_json"] else {},
            thumbnail_path=row["thumbnail_path"],
            embedding_id=row["embedding_id"],
        )
