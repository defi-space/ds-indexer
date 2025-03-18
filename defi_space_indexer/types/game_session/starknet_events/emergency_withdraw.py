# generated by DipDup 8.2.1

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class EmergencyWithdrawPayload(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    user: int
    amount: int
    block_timestamp: int
