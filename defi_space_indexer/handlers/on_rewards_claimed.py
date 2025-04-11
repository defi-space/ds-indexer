from defi_space_indexer import models as models
from defi_space_indexer.types.game_session.starknet_events.rewards_claimed import RewardsClaimedPayload
from dipdup.context import HandlerContext
from dipdup.models.starknet import StarknetEvent


async def on_rewards_claimed(
    ctx: HandlerContext,
    event: StarknetEvent[RewardsClaimedPayload],
) -> None:
    # Extract data from event payload
    user_address = f'0x{event.payload.user:x}'
    amount = event.payload.amount
    block_timestamp = event.payload.block_timestamp
    
    # Get session address and transaction hash from event data
    session_address = event.data.from_address
    transaction_hash = event.data.transaction_hash
    
    # Get game session from database
    session = await models.GameSession.get_or_none(address=session_address)
    if not session:
        ctx.logger.warning(f"Game session {session_address} not found when processing rewards claimed")
        return
    
    # Create game event record for tracking
    await models.GameEvent.create(
        transaction_hash=transaction_hash,
        created_at=block_timestamp,
        event_type=models.GameEventType.REWARDS_CLAIMED,
        user_address=user_address,
        amount=amount,
        session=session,
    )
    
    # Update user stakes to reflect claimed rewards (if they exist)
    user_stakes = await models.UserStake.filter(
        user_address=user_address,
        session_address=session_address
    )
    
    if user_stakes:
        # If the user has stakes, distribute the rewards proportionally
        total_stakes = sum(stake.amount for stake in user_stakes)
        
        if total_stakes > 0:
            # Distribute proportionally to stake amounts
            for stake in user_stakes:
                # Calculate proportional reward
                stake_proportion = stake.amount / total_stakes
                proportional_reward = int(amount * stake_proportion)
                
                stake.claimed_rewards += proportional_reward
                stake.updated_at = block_timestamp
                await stake.save()
                
                ctx.logger.debug(
                    f"Updated stake reward: user={user_address}, agent={stake.agent_index}, "
                    f"window={stake.stake_window_index}, amount={proportional_reward}"
                )
        else:
            ctx.logger.warning(
                f"User {user_address} has stakes with zero total amount, assigning rewards equally"
            )
            # If total stake is 0, distribute equally
            per_stake_amount = amount // len(user_stakes)
            for stake in user_stakes:
                stake.claimed_rewards += per_stake_amount
                stake.updated_at = block_timestamp
                await stake.save()
    else:
        ctx.logger.warning(
            f"No stakes found for user {user_address} in session {session_address} when claiming rewards"
        )
    
    ctx.logger.info(
        f"Rewards claimed: user={user_address}, session={session_address}, amount={amount}"
    )