from defi_space_indexer import models as models
from defi_space_indexer.types.game_session.starknet_events.game_over import GameOverPayload
from dipdup.context import HandlerContext
from dipdup.models.starknet import StarknetEvent


async def on_game_over(
    ctx: HandlerContext,
    event: StarknetEvent[GameOverPayload],
) -> None:
    # Extract data from event payload
    winning_agent_index = event.payload.winning_agent_index
    burn_fee_amount = event.payload.burn_fee_amount
    platform_fee_amount = event.payload.platform_fee_amount
    total_fees_amount = event.payload.total_fees_amount
    total_rewards = event.payload.total_rewards
    block_timestamp = event.payload.block_timestamp
    
    # Get session address from event data
    session_address = event.data.from_address
    transaction_hash = event.data.transaction_hash
    
    # Get game session from database
    session = await models.GameSession.get_or_none(address=session_address)
    if not session:
        ctx.logger.warning(f"Game session {session_address} not found when processing game over event")
        return
    
    # Update the game session
    session.game_over = True
    session.winning_agent_index = winning_agent_index
    session.total_rewards = total_rewards
    session.ended_at = block_timestamp
    session.updated_at = block_timestamp
    await session.save()
    
    # Create a game event record for the game over event
    await models.GameEvent.create(
        transaction_hash=transaction_hash,
        created_at=block_timestamp,
        event_type=models.GameEventType.GAME_OVER,
        user_address=session.owner,  # Use the owner address since this is a system event
        amount=total_rewards,  # The total rewards amount is the most relevant amount
        session=session,
    )
    
    # Log game completion details
    ctx.logger.info(
        f"Game over: session={session_address}, winning_agent={winning_agent_index}, "
        f"burn_fee={burn_fee_amount}, platform_fee={platform_fee_amount}, "
        f"total_fees={total_fees_amount}, total_rewards={total_rewards}"
    )