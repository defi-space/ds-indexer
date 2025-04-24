from defi_space_indexer import models as models
from defi_space_indexer.types.game_session.starknet_events.user_unstaked import UserUnstakedPayload
from dipdup.context import HandlerContext
from dipdup.models.starknet import StarknetEvent


async def on_user_unstaked(
    ctx: HandlerContext,
    event: StarknetEvent[UserUnstakedPayload],
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
        ctx.logger.warning(f"Session {session_address} not found when processing user unstake")
        return
    
    # Get agent from database
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
        ctx.logger.warning(
            f"Agent with index={agent_index}, session={session_address} not found when processing unstake"
        )
        return
    
    # Remove total_staked update - this is handled by the on_agent_updated handler
    # to avoid double-counting
    agent.updated_at = block_timestamp
    await agent.save()
    
    # Get the user stake record
    user_stake = await models.UserStake.get_or_none(
        user_address=user_address,
        agent_index=agent_index,
        stake_window_index=window_index,
        session_address=session_address
    )
    
    # Get stake window
    stake_window = await models.StakeWindow.get_or_none(
        session_address=session_address,
        index=window_index
    )
    
    # Update stake window's total staked if it exists
    if stake_window:
        if stake_window.total_staked >= amount:
            stake_window.total_staked -= amount
        else:
            ctx.logger.warning(
                f"Stake window {window_index} has less total staked ({stake_window.total_staked}) "
                f"than unstake amount ({amount}). Setting to 0."
            )
            stake_window.total_staked = 0
        
        # Add warning if unstaking in an inactive window
        if not stake_window.is_active:
            ctx.logger.warning(
                f"User {user_address} unstaked in inactive window {window_index} "
                f"for session {session_address}. This may be a frontend timing issue."
            )
        
        stake_window.updated_at = block_timestamp
        await stake_window.save()
    else:
        ctx.logger.warning(f"Stake window {window_index} not found for session {session_address}")
    
    if user_stake:
        # If the unstake amount is equal to or greater than the staked amount, remove the stake
        if amount >= user_stake.amount:
            await user_stake.delete()
            ctx.logger.info(f"Deleted user stake record for user={user_address}, agent={agent_index}, window={window_index}")
        else:
            # Otherwise, reduce the staked amount
            user_stake.amount -= amount
            user_stake.updated_at = block_timestamp
            await user_stake.save()
            ctx.logger.info(
                f"Updated user stake record: user={user_address}, agent={agent_index}, "
                f"window={window_index}, new_amount={user_stake.amount}"
            )
    else:
        ctx.logger.warning(
            f"UserStake record not found for user={user_address}, agent={agent_index}, "
            f"window={window_index}, session={session_address} when processing unstake"
        )
    
    # Create game event record for unstake
    await models.GameEvent.create(
        transaction_hash=transaction_hash,
        created_at=block_timestamp,
        event_type=models.GameEventType.UNSTAKE,
        user_address=user_address,
        agent_index=agent_index,
        stake_window_index=window_index,
        amount=amount,
        session=session,
    )
    
    ctx.logger.info(
        f"User unstaked: user={user_address}, agent={agent_index}, session={session_address}, "
        f"window={window_index}, amount={amount}"
    )