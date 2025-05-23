# generated by DipDup 8.2.1

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class OwnerUpdatedPayload(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    previous_owner: int
    new_owner: int
    factory_address: int
    block_timestamp: int
