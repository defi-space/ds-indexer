from defi_space_indexer.models.farming_models import Powerplant
from defi_space_indexer.types.farming_factory.starknet_events.powerplant_initialized import PowerplantInitializedPayload
from dipdup.context import HandlerContext
from dipdup.models.starknet import StarknetEvent


async def on_powerplant_initialized(
    ctx: HandlerContext,
    event: StarknetEvent[PowerplantInitializedPayload],
) -> None:
    """Handle PowerplantInitialized event from Powerplant contract."""
    powerplant = Powerplant(
        address=event.data.from_address,
        reactor_count=0,
        total_value_locked_usd=0,
        owner=hex(event.payload.owner),
        reactor_class_hash=hex(event.payload.reactor_class_hash),
        config_history=[],
        created_at=event.payload.block_timestamp,
        updated_at=event.payload.block_timestamp,
    )
    await powerplant.save()