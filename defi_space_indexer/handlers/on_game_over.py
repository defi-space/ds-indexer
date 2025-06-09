from dipdup.context import HandlerContext
from dipdup.models.starknet import StarknetEvent

from defi_space_indexer import models as models
from defi_space_indexer.types.game_session.starknet_events.game_over import GameOverPayload


async def on_game_over(
    ctx: HandlerContext,
    event: StarknetEvent[GameOverPayload],
) -> None:
    # Extract data from event payload
    winning_agent_index = event.payload.winning_agent_index
    burn_fee_amount = event.payload.burn_fee_amount
    platform_fee_amount = event.payload.platform_fee_amount
    total_fees_amount = event.payload.total_fees_amount
    total_score = event.payload.total_score
    total_rewards = event.payload.total_rewards
    block_timestamp = event.payload.block_timestamp

    # Get session address from event data
    session_address = event.data.from_address
    transaction_hash = event.data.transaction_hash

    # Get game session from database
    session = await models.GameSession.get_or_none(address=session_address)
    if not session:
        ctx.logger.warning(f'Game session {session_address} not found when processing game over event')
        return

    # Update the game session
    session.game_over = True
    session.winning_agent_index = winning_agent_index
    session.total_rewards = total_rewards
    session.game_end_timestamp = block_timestamp
    session.ended_at = block_timestamp
    session.updated_at = block_timestamp
    await session.save()

    # Update the winning agent's total score
    winning_agent = None
    for agent_address in session.agents_list:
        agent_obj = await models.Agent.get_or_none(address=agent_address, session_address=session_address)
        if agent_obj and agent_obj.agent_index == winning_agent_index:
            winning_agent = agent_obj
            break

    if winning_agent:
        winning_agent.total_score = total_score
        winning_agent.updated_at = block_timestamp
        await winning_agent.save()
        ctx.logger.info(f'Updated winning agent {winning_agent_index} total score: {total_score}')

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
        f'Game over: session={session_address}, winning_agent={winning_agent_index}, '
        f'burn_fee={burn_fee_amount}, platform_fee={platform_fee_amount}, '
        f'total_fees={total_fees_amount}, total_score={total_score}, total_rewards={total_rewards}'
    )
