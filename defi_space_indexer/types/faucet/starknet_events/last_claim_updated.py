# generated by DipDup 8.2.1

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class LastClaimUpdatedPayload(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    user_address: int
    previous_timestamp: int
    new_timestamp: int
    block_timestamp: int
