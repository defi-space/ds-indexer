from dipdup.context import HandlerContext
from dipdup.models.starknet import StarknetEvent
from defi_space_indexer.models.game_models import GameFactory
from defi_space_indexer.types.game_factory.starknet_events.ownership_transferred import OwnershipTransferredPayload

async def on_game_ownership_transferred(
    ctx: HandlerContext,
    event: StarknetEvent[OwnershipTransferredPayload],
) -> None:
    """Handle OwnershipTransferred event from GameFactory contract.
    
    Updates the owner of the game factory. Important for:
    - Tracking ownership changes
    - Maintaining administrative history
    - Monitoring protocol control
    """
    factory = await GameFactory.get_or_none(address=hex(event.payload.factory_address))
    if factory is None:
        ctx.logger.info(f"GameFactory not found: {hex(event.payload.factory_address)}")
        return
    
    # Record configuration change
    old_owner = factory.owner
    new_owner = hex(event.payload.new_owner)
    
    factory.config_history.append({
        'field': 'owner',
        'old_value': old_owner,
        'new_value': new_owner,
        'timestamp': event.payload.block_timestamp
    })
    
    # Update current state
    factory.owner = new_owner
    factory.updated_at = event.payload.block_timestamp
    
    await factory.save() 