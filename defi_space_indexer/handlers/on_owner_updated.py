from dipdup.context import HandlerContext
from dipdup.models.starknet import StarknetEvent
from defi_space_indexer.models.amm_models import Factory
from defi_space_indexer.types.amm_factory.starknet_events.owner_updated import OwnerUpdatedPayload

async def on_owner_updated(
    ctx: HandlerContext,
    event: StarknetEvent[OwnerUpdatedPayload],
) -> None:
    """Handle OwnerUpdated event from Factory contract."""
    factory = await Factory.get_or_none(address=event.data.from_address)
    if factory is None:
        ctx.logger.info(f"Factory not found: {event.data.from_address}")
        return
    factory.owner = hex(event.payload.new_owner)
    factory.updated_at = event.payload.block_timestamp
    
    factory.config_history.append({
        'field': 'owner',
        'old_value': hex(event.payload.previous_owner),
        'new_value': hex(event.payload.new_owner),
        'timestamp': event.payload.block_timestamp
    })
    await factory.save()