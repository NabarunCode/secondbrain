from enum import Enum


class AssetType(str, Enum):
    PHOTO = "photo"
    DOCUMENT = "document"
    NOTE = "note"
    AUDIO = "audio"
    VIDEO = "video"
    OTHER = "other"