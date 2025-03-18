from dipdup.context import HandlerContext
from dipdup.models.starknet import StarknetEvent
from defi_space_indexer.models.game_models import GameSession
from defi_space_indexer.types.game_session.starknet_events.game_suspended import GameSuspendedPayload

async def on_game_suspended(
    ctx: HandlerContext,
    event: StarknetEvent[GameSuspendedPayload],
) -> None:
    """Handle GameSuspended event from GameSession contract.
    
    Updates game session status when suspended. Important for:
    - Tracking game lifecycle
    - Monitoring exceptional status changes
    - Alerting to administration actions
    """
    session = await GameSession.get_or_none(address=event.data.from_address)
    if session is None:
        ctx.logger.info(f"GameSession not found: {event.data.from_address}")
        return
    
    # Update game session status
    session.is_suspended = True
    session.updated_at = event.payload.block_timestamp
    
    # Record the suspension in config history
    session.config_history.append({
        'action': 'game_suspended',
        'timestamp': event.payload.block_timestamp
    })
    
    await session.save() 