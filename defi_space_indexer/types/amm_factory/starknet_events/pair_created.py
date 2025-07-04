# generated by DipDup 8.4.1

from __future__ import annotations

from pydantic import BaseModel
from pydantic import ConfigDict


class PairCreatedPayload(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    token0: int
    token1: int
    pair: int
    total_pairs: int
    pair_contract_class_hash: int
    factory_address: int
    game_session_id: int
    block_timestamp: int
