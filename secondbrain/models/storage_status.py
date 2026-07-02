from enum import Enum


class StorageStatus(str, Enum):
    DISCOVERED = "discovered"

    HASHING = "hashing"

    DEDUP_CHECK = "dedup_check"

    PROCESSING = "processing"

    UPLOADING = "uploading"

    VERIFYING = "verifying"

    VERIFIED = "verified"

    DUPLICATE = "duplicate"

    FAILED = "failed"