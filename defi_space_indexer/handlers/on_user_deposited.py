from dipdup.context import HandlerContext
from dipdup.models.starknet import StarknetEvent

from defi_space_indexer import models as models
from defi_space_indexer.types.game_session.starknet_events.user_deposited import UserDepositedPayload


async def on_user_deposited(
    ctx: HandlerContext,
    event: StarknetEvent[UserDepositedPayload],
) -> None:
    # Extract data from event payload
    user_address = f'0x{event.payload.user:x}'
    agent_index = event.payload.agent_index
    amount = event.payload.amount
    old_score = event.payload.old_score
    new_score = event.payload.new_score
    block_timestamp = event.payload.block_timestamp

    # Get session address from event data
    session_address = event.data.from_address
    transaction_hash = event.data.transaction_hash

    # Get session from database
    session = await models.GameSession.get_or_none(address=session_address)
    if not session:
        ctx.logger.warning(f'Session {session_address} not found when processing user deposit')
        return

    # Find the agent by index in the session's agents list
    agent = None
    for agent_address in session.agents_list:
        agent_obj = await models.Agent.get_or_none(address=agent_address, session_address=session_address)
        if agent_obj and agent_obj.agent_index == agent_index:
            agent = agent_obj
            break

    if not agent:
        ctx.logger.warning(f'Agent with index {agent_index} not found for session {session_address}')
        return

    # Update agent timestamp - total_deposited is handled by the on_agent_updated handler
    agent.updated_at = block_timestamp
    await agent.save()

    # Check if a user deposit record already exists
    user_deposit = await models.UserDeposit.get_or_none(
        user_address=user_address,
        agent_index=agent_index,
        session_address=session_address,
    )

    if user_deposit:
        # Update existing deposit
        user_deposit.amount += amount
        user_deposit.accumulated_score = new_score
        user_deposit.last_score_update = block_timestamp
        user_deposit.updated_at = block_timestamp
        await user_deposit.save()
        ctx.logger.info(
            f'Updated user deposit: user={user_address}, agent={agent_index}, session={session_address}, '
            f'new_amount={user_deposit.amount}, new_score={new_score}'
        )
    else:
        # Create new user deposit record
        await models.UserDeposit.create(
            user_address=user_address,
            agent_index=agent_index,
            session_address=session_address,
            amount=amount,
            accumulated_score=new_score,
            last_score_update=block_timestamp,
            created_at=block_timestamp,
            updated_at=block_timestamp,
            session=session,
        )
        ctx.logger.info(
            f'Created new user deposit: user={user_address}, agent={agent_index}, session={session_address}, '
            f'amount={amount}, score={new_score}'
        )

    # Create game event record
    await models.GameEvent.create(
        transaction_hash=transaction_hash,
        created_at=block_timestamp,
        event_type=models.GameEventType.USER_DEPOSITED,
        user_address=user_address,
        agent_index=agent_index,
        amount=amount,
        old_score=old_score,
        new_score=new_score,
        session=session,
    )

    ctx.logger.info(
        f'User deposited: user={user_address}, agent={agent_index}, session={session_address}, '
        f'amount={amount}, old_score={old_score}, new_score={new_score}'
    )
