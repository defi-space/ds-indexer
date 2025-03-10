from dipdup.context import HandlerContext
from dipdup.models.starknet import StarknetEvent
from defi_space_indexer.models.farming_models import Reactor
from defi_space_indexer.types.farming_reactor.starknet_events.ownership_transferred import OwnershipTransferredPayload

async def on_reactor_ownership_transferred(
    ctx: HandlerContext,
    event: StarknetEvent[OwnershipTransferredPayload],
) -> None:
    """Handle OwnershipTransferred event from Reactor contract."""
    reactor = await Reactor.get_or_none(address=event.data.from_address)
    if reactor is None:
        ctx.logger.info(f"Reactor not found: {event.data.from_address}")
        return
    reactor.owner = hex(event.payload.new_owner)
    reactor.updated_at = event.payload.block_timestamp
    reactor.config_history.append({
        'field': 'owner',
        'old_value': hex(event.payload.previous_owner),
        'new_value': hex(event.payload.new_owner),
        'timestamp': event.payload.block_timestamp,
    })
    await reactor.save()