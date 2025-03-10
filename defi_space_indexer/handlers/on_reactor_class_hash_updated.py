from dipdup.context import HandlerContext
from dipdup.models.starknet import StarknetEvent
from defi_space_indexer.models.farming_models import Powerplant
from defi_space_indexer.types.farming_factory.starknet_events.reactor_class_hash_updated import ReactorClassHashUpdatedPayload

async def on_reactor_class_hash_updated(
    ctx: HandlerContext,
    event: StarknetEvent[ReactorClassHashUpdatedPayload],
) -> None:
    """Handle ReactorClassHashUpdated event from Powerplant contract."""
    powerplant = await Powerplant.get_or_none(address=event.data.from_address)
    if powerplant is None:
        ctx.logger.info(f"Powerplant not found: {event.data.from_address}")
        return
    powerplant.reactor_class_hash = hex(event.payload.new_hash)
    powerplant.updated_at = event.payload.block_timestamp
    
    powerplant.config_history.append({
        'field': 'reactor_class_hash',
        'old_value': hex(event.payload.old_hash),
        'new_value': hex(event.payload.new_hash),
        'timestamp': event.payload.block_timestamp,
    })
    await powerplant.save()