# generated by DipDup 8.2.1

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class AddedToWhitelistPayload(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    address: int
    block_timestamp: int
