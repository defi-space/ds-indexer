# generated by DipDup 8.2.1

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class ClaimPayload(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    sender: int
    token: int
    amount: int
    faucet_address: int
    total_token_amount: int
    claimed_at: int
    block_timestamp: int
