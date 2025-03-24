from dipdup.context import HandlerContext
from dipdup.models.starknet import StarknetEvent
from defi_space_indexer.models.game_models import GameSession, UserStake, GameEvent, GameEventType, StakeWindow
from defi_space_indexer.types.game_session.starknet_events.user_staked import UserStakedPayload

async def on_user_staked(
    ctx: HandlerContext,
    event: StarknetEvent[UserStakedPayload],
) -> None:
    """Handle UserStaked event from GameSession contract.
    
    Tracks a user staking tokens for an agent. Important for:
    - Recording stake positions
    - Updating agent allocations
    - Tracking game participation
    """
    session = await GameSession.get_or_none(address=event.data.from_address)
    if session is None:
        ctx.logger.info(f"GameSession not found: {event.data.from_address}")
        return
        
    user_address = hex(event.payload.user)
    agent_index = event.payload.agent_index
    amount = event.payload.amount
    window_index = event.payload.window_index
    
    # Get or create user stake
    user_stake = await UserStake.get_or_none(
        session_address=event.data.from_address,
        user_address=user_address,
        agent_index=agent_index
    )
    
    if user_stake is None:
        user_stake = UserStake(
            session_address=event.data.from_address,
            user_address=user_address,
            agent_index=agent_index,
            staked_amount=amount,
            claimed_rewards=0,
            created_at=event.payload.block_timestamp,
            updated_at=event.payload.block_timestamp,
            session=session,
        )
    else:
        user_stake.staked_amount += amount
        user_stake.updated_at = event.payload.block_timestamp
    
    await user_stake.save()
    
    # Record stake event
    stake_event = GameEvent(
        transaction_hash=event.data.transaction_hash,
        created_at=event.payload.block_timestamp,
        event_type=GameEventType.STAKE,
        user_address=user_address,
        agent_index=agent_index,
        window_index=window_index,
        amount=amount,
        session=session,
        user_stake=user_stake,
    )
    await stake_event.save()
    
    # Update session total staked
    session.total_staked += amount
    session.updated_at = event.payload.block_timestamp
    await session.save()
    
    # Update window total staked
    window = await StakeWindow.get_or_none(
        session_address=event.data.from_address,
        window_index=window_index
    )
    
    if window:
        window.total_staked += amount
        window.updated_at = event.payload.block_timestamp
        await window.save() 