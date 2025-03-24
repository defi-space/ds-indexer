from dipdup.context import HandlerContext
from dipdup.models.starknet import StarknetEvent
from defi_space_indexer.models.game_models import GameSession, UserStake, GameEvent, GameEventType, StakeWindow
from defi_space_indexer.types.game_session.starknet_events.user_unstaked import UserUnstakedPayload

async def on_user_unstaked(
    ctx: HandlerContext,
    event: StarknetEvent[UserUnstakedPayload],
) -> None:
    """Handle UserUnstaked event from GameSession contract.
    
    Tracks a user unstaking tokens from an agent. Important for:
    - Recording withdrawal of stake
    - Updating agent allocations
    - Tracking game participation changes
    """
    session = await GameSession.get_or_none(address=event.data.from_address)
    if session is None:
        ctx.logger.error(f"GameSession not found: {event.data.from_address}")
        return
        
    user_address = hex(event.payload.user)
    agent_index = event.payload.agent_index
    amount = event.payload.amount
    window_index = event.payload.window_index
        
    try:
        # Get user stake
        user_stake = await UserStake.get_or_none(
            session_address=event.data.from_address,
            user_address=user_address,
            agent_index=agent_index
        )
        
        if user_stake is None:
            ctx.logger.error(f"UserStake not found for unstaking: {user_address} in {event.data.from_address}")
            return
        
        # Update user stake
        user_stake.staked_amount -= amount
        user_stake.updated_at = event.payload.block_timestamp
        
        if user_stake.staked_amount <= 0:
            await user_stake.delete()
        else:
            await user_stake.save()
        
        # Record unstake event
        unstake_event = GameEvent(
            transaction_hash=event.data.transaction_hash,
            created_at=event.payload.block_timestamp,
            event_type=GameEventType.UNSTAKE,
            user_address=user_address,
            agent_index=agent_index,
            window_index=window_index,
            amount=amount,
            session=session,
            user_stake=user_stake if user_stake.staked_amount > 0 else None,
        )
        await unstake_event.save()
        
        # Update session total staked
        session.total_staked -= amount
        session.updated_at = event.payload.block_timestamp
        await session.save()
        
        # Update window total staked
        window = await StakeWindow.get_or_none(
            session_address=event.data.from_address,
            window_index=window_index
        )
        
        if window:
            window.total_staked -= amount
            await window.save()
        
        # Trigger time-based fields update
        await ctx.fire_hook(
            'active_staking_window',
            update_all=False,
            session_address=event.data.from_address
        )
        
    except Exception as e:
        ctx.logger.error(f"Error processing UserUnstaked event: {str(e)}")
        raise 