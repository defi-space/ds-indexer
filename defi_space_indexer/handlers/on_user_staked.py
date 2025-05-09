from defi_space_indexer import models as models
from defi_space_indexer.types.game_session.starknet_events.user_staked import UserStakedPayload
from dipdup.context import HandlerContext
from dipdup.models.starknet import StarknetEvent


async def on_user_staked(
    ctx: HandlerContext,
    event: StarknetEvent[UserStakedPayload],
) -> None:
    # Extract data from event payload
    user_address = f'0x{event.payload.user:x}'
    agent_index = event.payload.agent_index
    amount = event.payload.amount
    window_index = event.payload.window_index
    block_timestamp = event.payload.block_timestamp
    
    # Get session address from event data
    session_address = event.data.from_address
    transaction_hash = event.data.transaction_hash
    
    # Get session from database
    session = await models.GameSession.get_or_none(address=session_address)
    if not session:
        ctx.logger.warning(f"Session {session_address} not found when processing user stake")
        return
    
    # Get stake window
    stake_window = await models.StakeWindow.get_or_none(
        session_address=session_address,
        index=window_index
    )
    
    if not stake_window:
        ctx.logger.warning(f"Stake window {window_index} not found for session {session_address}")
        # Continue processing as we can still record the agent and stake information
    
    # Find the agent by index in the session's agents list
    agent = None
    for agent_address in session.agents_list:
        agent_obj = await models.Agent.get_or_none(
            address=agent_address,
            session_address=session_address
        )
        if agent_obj and agent_obj.agent_index == agent_index:
            agent = agent_obj
            break
    
    if not agent:
        ctx.logger.warning(f"Agent with index {agent_index} not found for session {session_address}")
        return
    
    # Remove total_staked update - this is handled by the on_agent_updated handler
    # to avoid double-counting
    agent.updated_at = block_timestamp
    await agent.save()
    
    # Update stake window's total staked if it exists
    if stake_window:
        stake_window.total_staked += amount
        stake_window.updated_at = block_timestamp
        
        # Add warning if staking in an inactive window
        if not stake_window.is_active:
            ctx.logger.warning(
                f"User {user_address} staked in inactive window {window_index} "
                f"for session {session_address}. This may be a frontend timing issue."
            )
        
        await stake_window.save()
    
    # Check if a user stake record already exists
    user_stake = await models.UserStake.get_or_none(
        user_address=user_address,
        agent_index=agent_index,
        stake_window_index=window_index,
        session_address=session_address
    )
    
    if user_stake:
        # Update existing stake
        user_stake.amount += amount
        user_stake.updated_at = block_timestamp
        await user_stake.save()
        ctx.logger.info(
            f"Updated user stake: user={user_address}, agent={agent_index}, session={session_address}, "
            f"window={window_index}, new_amount={user_stake.amount}"
        )
    else:
        # Create new user stake record
        await models.UserStake.create(
            user_address=user_address,
            agent_index=agent_index,
            stake_window_index=window_index,
            session_address=session_address,
            amount=amount,
            created_at=block_timestamp,
            updated_at=block_timestamp,
            session=session,
        )
        ctx.logger.info(
            f"Created new user stake: user={user_address}, agent={agent_index}, session={session_address}, "
            f"window={window_index}, amount={amount}"
        )
    
    # Create game event record
    await models.GameEvent.create(
        transaction_hash=transaction_hash,
        created_at=block_timestamp,
        event_type=models.GameEventType.STAKE,
        user_address=user_address,
        agent_index=agent_index,
        stake_window_index=window_index,
        amount=amount,
        session=session,
    )
    
    ctx.logger.info(
        f"User staked: user={user_address}, agent={agent_index}, session={session_address}, "
        f"window={window_index}, amount={amount}"
    )