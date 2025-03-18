from dipdup.context import HandlerContext
from dipdup.models.starknet import StarknetEvent
from defi_space_indexer.models.game_models import GameFactory
from defi_space_indexer.types.game_factory.starknet_events.game_session_class_hash_updated import GameSessionClassHashUpdatedPayload

async def on_game_session_class_hash_updated(
    ctx: HandlerContext,
    event: StarknetEvent[GameSessionClassHashUpdatedPayload],
) -> None:
    """Handle GameSessionClassHashUpdated event from GameFactory contract.
    
    Updates the implementation hash for game sessions. Important for:
    - Tracking protocol upgrades
    - Monitoring implementation changes
    - Maintaining configuration history
    """
    factory = await GameFactory.get_or_none(address=hex(event.payload.factory_address))
    if factory is None:
        ctx.logger.info(f"GameFactory not found: {hex(event.payload.factory_address)}")
        return
    
    # Record configuration change
    old_hash = hex(event.payload.old_hash)
    new_hash = hex(event.payload.new_hash)
    
    factory.config_history.append({
        'field': 'game_session_class_hash',
        'old_value': old_hash,
        'new_value': new_hash,
        'timestamp': event.payload.block_timestamp
    })
    
    # Update current state
    factory.game_session_class_hash = new_hash
    factory.updated_at = event.payload.block_timestamp
    
    await factory.save() 