# generated by DipDup 8.2.1

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class GameSuspendedPayload(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    block_timestamp: int
