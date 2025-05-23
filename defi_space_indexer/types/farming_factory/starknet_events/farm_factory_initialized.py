# generated by DipDup 8.2.1

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class FarmFactoryInitializedPayload(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    farm_factory: int
    owner: int
    farm_class_hash: int
    block_timestamp: int
