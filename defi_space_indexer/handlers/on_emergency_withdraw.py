from dipdup.context import HandlerContext
from dipdup.models.starknet import StarknetEvent
from defi_space_indexer.models.game_models import GameSession, UserGameStake, GameEvent, GameEventType
from defi_space_indexer.types.game_session.starknet_events.emergency_withdraw import EmergencyWithdrawPayload

async def on_emergency_withdraw(
    ctx: HandlerContext,
    event: StarknetEvent[EmergencyWithdrawPayload],
) -> None:
    """Handle EmergencyWithdraw event from GameSession contract.
    
    Tracks emergency withdrawal of user stakes. Important for:
    - Handling exceptional circumstances
    - Recording emergency actions
    - Managing stake positions during emergencies
    """
    session = await GameSession.get_or_none(address=event.data.from_address)
    if session is None:
        ctx.logger.info(f"GameSession not found: {event.data.from_address}")
        return
        
    user_address = hex(event.payload.user)
    amount = event.payload.amount
    
    # Record emergency withdraw event
    emergency_event = GameEvent(
        transaction_hash=event.data.transaction_hash,
        created_at=event.payload.block_timestamp,
        event_type=GameEventType.EMERGENCY_WITHDRAW,
        user_address=user_address,
        amount=amount,
        session=session,
        user_stake=None,  # No specific stake as this removes all positions
    )
    await emergency_event.save()
    
    # Find and remove all user stakes
    user_stakes = await UserGameStake.filter(
        session_address=event.data.from_address,
        user_address=user_address
    )
    
    total_withdrawn = 0
    for stake in user_stakes:
        total_withdrawn += stake.staked_amount
        await stake.delete()
    
    # Update session total staked
    session.total_staked -= total_withdrawn
    session.updated_at = event.payload.block_timestamp
    await session.save() 