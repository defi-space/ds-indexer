from dipdup.context import HandlerContext
from dipdup.models.starknet import StarknetEvent
from defi_space_indexer.models.game_models import GameSession
from defi_space_indexer.types.game_session.starknet_events.game_over import GameOverPayload

async def on_game_over(
    ctx: HandlerContext,
    event: StarknetEvent[GameOverPayload],
) -> None:
    """Handle GameOver event from GameSession contract.
    
    Updates game session when completed with a winner. Important for:
    - Recording game outcomes
    - Finalizing reward distributions
    - Calculating performance metrics
    """
    session = await GameSession.get_or_none(address=event.data.from_address)
    if session is None:
        ctx.logger.info(f"GameSession not found: {event.data.from_address}")
        return
    
    # Update game session status
    session.is_over = True
    session.winning_agent_index = event.payload.winning_agent_index
    session.burn_fee_amount = event.payload.burn_fee_amount
    session.platform_fee_amount = event.payload.platform_fee_amount
    session.total_fees_amount = event.payload.total_fees_amount
    session.total_rewards = event.payload.total_rewards
    session.updated_at = event.payload.block_timestamp
    session.ended_at = event.payload.block_timestamp
    
    # Record the game end in config history
    session.config_history.append({
        'action': 'game_over',
        'winning_agent': event.payload.winning_agent_index,
        'timestamp': event.payload.block_timestamp
    })
    
    await session.save() 