# generated by DipDup 8.4.1

from __future__ import annotations

from pydantic import BaseModel
from pydantic import ConfigDict


class ConfigUpdatedPayload(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    field_name: int
    old_value: int
    new_value: int
    pair_address: int
    block_timestamp: int
