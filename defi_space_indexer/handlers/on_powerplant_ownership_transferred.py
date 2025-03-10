from dipdup.context import HandlerContext
from dipdup.models.starknet import StarknetEvent
from defi_space_indexer.models.farming_models import Powerplant
from defi_space_indexer.types.farming_factory.starknet_events.ownership_transferred import OwnershipTransferredPayload

async def on_powerplant_ownership_transferred(
    ctx: HandlerContext,
    event: StarknetEvent[OwnershipTransferredPayload],
) -> None:
    """Handle OwnershipTransferred event from Powerplant contract."""
    powerplant = await Powerplant.get_or_none(address=event.data.from_address)
    if powerplant is None:
        ctx.logger.info(f"Powerplant not found: {event.data.from_address}")
        return
    powerplant.owner = hex(event.payload.new_owner)
    powerplant.updated_at = event.payload.block_timestamp
    
    powerplant.config_history.append({
        'field': 'owner',
        'old_value': hex(event.payload.previous_owner),
        'new_value': hex(event.payload.new_owner),
        'timestamp': event.payload.block_timestamp,
    })
    await powerplant.save()