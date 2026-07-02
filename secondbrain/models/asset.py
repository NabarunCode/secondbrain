# secondbrain/models/asset.py

from datetime import datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from .asset_type import AssetType
from .storage_status import StorageStatus


# ----------------------------------------------------------------------
# Type aliases
# ----------------------------------------------------------------------

AssetId = str


class Asset(BaseModel):
    """
    Core SecondBrain asset model.

    Represents one logical asset tracked by SecondBrain,
    regardless of whether the underlying blob has already
    been uploaded to Hugging Face Buckets.
    """

    # ==========================================================
    # Identity
    # ==========================================================

    id: AssetId

    # ==========================================================
    # Classification
    # ==========================================================

    asset_type: AssetType

    # ==========================================================
    # Workflow state
    # ==========================================================

    storage_status: StorageStatus

    # Stage where processing failed.
    #
    # Examples:
    #   sha256
    #   dedup_check
    #   metadata
    #   thumbnail
    #   upload
    #   verify
    #
    failure_stage: str | None = None

    # Points to the original asset if this
    # asset is determined to be a duplicate.
    #
    duplicate_of: AssetId | None = None

    # ==========================================================
    # Local file information
    # ==========================================================

    # Original filename.
    filename: str

    # Original local filesystem location.
    #
    # Example:
    # D:\Photos\Kalpa\IMG001.JPG
    #
    local_path: Path | None = None

    # ==========================================================
    # User metadata
    # ==========================================================

    title: str | None = None

    description: str | None = None

    tags: list[str] = Field(default_factory=list)

    # ==========================================================
    # HF Bucket storage information
    # ==========================================================

    # Nullable because an asset may not
    # have been uploaded yet.
    #
    bucket_name: str | None = None

    # Example:
    # photos/2026/kalpa/IMG001.JPG
    #
    object_key: str | None = None

    # ==========================================================
    # Physical file information
    # ==========================================================

    # Example:
    # image/jpeg
    #
    mime_type: str

    # File size in bytes.
    #
    size_bytes: int

    # SHA256 checksum.
    #
    # Nullable because the asset enters
    # the database before hashing begins.
    #
    sha256: str | None = None

    # ==========================================================
    # Timestamps
    # ==========================================================

    # Last modified timestamp of the
    # original file.
    #
    file_modified_at: datetime

    # Original creation date if known.
    #
    # Examples:
    #   EXIF DateTimeOriginal
    #   PDF metadata
    #   filesystem creation date
    #
    original_date: datetime | None = None

    # ==========================================================
    # Asset-specific metadata
    # ==========================================================

    metadata: dict[str, Any] = Field(
        default_factory=dict
    )

    # ==========================================================
    # Derived assets
    # ==========================================================

    # Example:
    # thumbnails/01JZFQ8N.jpg
    #
    thumbnail_path: str | None = None

    # Reserved for future semantic search.
    #
    embedding_id: str | None = None