from datetime import datetime

from secondbrain.models.asset import Asset
from secondbrain.models.asset_type import AssetType
from secondbrain.models.storage_status import StorageStatus


asset = Asset(
    id="01JZFQ8NK9R2QK4Q7P2M8C1YAB",

    asset_type=AssetType.PHOTO,

    storage_status=StorageStatus.DISCOVERED,

    filename="IMG001.JPG",

    mime_type="image/jpeg",

    size_bytes=14567342,

    file_modified_at=datetime.now()
)

print(f"\nID : {asset.id}")
print(f"Filename : {asset.filename}")
print(f"Size : {asset.size_bytes}")
print(f"Modified : {asset.file_modified_at}")
print(f"\nAsset details:\n{asset}\n")
print(f"\nAsset model dump:\n {asset.model_dump()}")
print(f"\nAsset model json:\n {asset.model_dump_json(indent=2)}\n")
