from dipdup.context import HandlerContext
from dipdup.models.starknet import StarknetEvent

from defi_space_indexer import models as models
from defi_space_indexer.types.game_session.starknet_events.rewards_claimed import RewardsClaimedPayload


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
        ctx.logger.warning(f'Game session {session_address} not found when processing rewards claimed')
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

    # Update user deposits to reflect claimed rewards (if they exist)
    user_deposits = await models.UserDeposit.filter(user_address=user_address, session_address=session_address)

    if user_deposits:
        # Log the reward claim for tracking purposes
        for deposit in user_deposits:
            deposit.updated_at = block_timestamp
            await deposit.save()

            ctx.logger.debug(
                f'Updated deposit timestamp for user={user_address}, agent={deposit.agent_index}, '
                f'session={session_address} due to reward claim'
            )
    else:
        ctx.logger.warning(
            f'No deposits found for user {user_address} in session {session_address} when claiming rewards'
        )

    ctx.logger.info(f'Rewards claimed: user={user_address}, session={session_address}, amount={amount}')
