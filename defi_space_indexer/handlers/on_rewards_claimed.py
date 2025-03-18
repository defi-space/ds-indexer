from dipdup.context import HandlerContext
from dipdup.models.starknet import StarknetEvent
from defi_space_indexer.models.game_models import GameSession, UserGameStake, GameEvent, GameEventType
from defi_space_indexer.types.game_session.starknet_events.rewards_claimed import RewardsClaimedPayload

async def on_rewards_claimed(
    ctx: HandlerContext,
    event: StarknetEvent[RewardsClaimedPayload],
) -> None:
    """Handle RewardsClaimed event from GameSession contract.
    
    Tracks claiming of rewards by users in a completed game. Important for:
    - Recording reward distributions
    - Tracking user winnings
    - Managing game outcomes
    """
    session = await GameSession.get_or_none(address=event.data.from_address)
    if session is None:
        ctx.logger.info(f"GameSession not found: {event.data.from_address}")
        return
        
    user_address = hex(event.payload.user)
    amount = event.payload.amount
    
    # Record reward claim event
    reward_event = GameEvent(
        transaction_hash=event.data.transaction_hash,
        created_at=event.payload.block_timestamp,
        event_type=GameEventType.REWARDS_CLAIMED,
        user_address=user_address,
        amount=amount,
        session=session,
        user_stake=None,  # No specific stake as rewards are per user across all stakes
    )
    await reward_event.save()
    
    # Update claimed rewards for all user stakes in the session
    user_stakes = await UserGameStake.filter(
        session_address=event.data.from_address,
        user_address=user_address
    )
    
    # If user has multiple stakes, distribute reward proportionally
    total_staked = sum(stake.staked_amount for stake in user_stakes)
    if total_staked > 0:
        for stake in user_stakes:
            # Calculate proportional reward amount
            stake_proportion = stake.staked_amount / total_staked
            proportional_reward = amount * stake_proportion
            
            # Update stake with claimed reward
            stake.claimed_rewards += proportional_reward
            stake.updated_at = event.payload.block_timestamp
            await stake.save() 