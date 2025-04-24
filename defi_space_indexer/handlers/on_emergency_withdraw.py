from defi_space_indexer import models as models
from defi_space_indexer.types.game_session.starknet_events.emergency_withdraw import EmergencyWithdrawPayload
from dipdup.context import HandlerContext
from dipdup.models.starknet import StarknetEvent


async def on_emergency_withdraw(
    ctx: HandlerContext,
    event: StarknetEvent[EmergencyWithdrawPayload],
) -> None:
    # Extract data from event payload
    user_address = f'0x{event.payload.user:x}'
    amount = event.payload.amount
    block_timestamp = event.payload.block_timestamp
    
    # Get session address from event data
    session_address = event.data.from_address
    transaction_hash = event.data.transaction_hash
    
    # Get game session from database
    session = await models.GameSession.get_or_none(address=session_address)
    if not session:
        ctx.logger.warning(f"Game session {session_address} not found when processing emergency withdrawal")
        return
    
    # Update session timestamp
    session.updated_at = block_timestamp
    await session.save()
    
    # Get all user stakes for this user in this session
    user_stakes = await models.UserStake.filter(
        user_address=user_address,
        session_address=session_address
    )
    
    # Remove all user stakes as this is an emergency withdrawal
    if user_stakes:
        # Get the list of affected agent indexes
        agent_indexes = set(stake.agent_index for stake in user_stakes)
        
        # Delete all user stakes for this user in this session
        for stake in user_stakes:
            await stake.delete()
        
        ctx.logger.info(
            f"Deleted {len(user_stakes)} UserStake records for user={user_address} "
            f"in session={session_address} due to emergency withdrawal"
        )
        
        # Update agent's updated_at timestamp but don't modify total_staked
        # total_staked is handled by the on_agent_updated handler
        for agent_index in agent_indexes:
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
            
            if agent:
                # Update timestamp only
                agent.updated_at = block_timestamp
                await agent.save()
                ctx.logger.info(
                    f"Updated timestamp for agent with index={agent_index}, session={session_address}"
                )
    
    # Create game event record for tracking
    await models.GameEvent.create(
        transaction_hash=transaction_hash,
        created_at=block_timestamp,
        event_type=models.GameEventType.EMERGENCY_WITHDRAW,
        user_address=user_address,
        amount=amount,
        session=session,
    )
    
    ctx.logger.info(
        f"Emergency withdraw processed: user={user_address}, session={session_address}, "
        f"amount={amount}"
    )