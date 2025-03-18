# generated by DipDup 8.2.1

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class UserUnstakedPayload(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    user: int
    agent_index: int
    amount: int
    window_index: int
    block_timestamp: int
