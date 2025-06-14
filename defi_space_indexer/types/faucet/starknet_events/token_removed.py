# generated by DipDup 8.4.1

from __future__ import annotations

from pydantic import BaseModel
from pydantic import ConfigDict


class TokenRemovedPayload(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    token: int
    block_timestamp: int
