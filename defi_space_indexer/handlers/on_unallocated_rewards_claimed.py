from dipdup.context import HandlerContext
from dipdup.models.starknet import StarknetEvent

from defi_space_indexer import models as models
from defi_space_indexer.types.farming_farm.starknet_events.unallocated_rewards_claimed import (
    UnallocatedRewardsClaimedPayload,
)


async def on_unallocated_rewards_claimed(
    ctx: HandlerContext,
    event: StarknetEvent[UnallocatedRewardsClaimedPayload],
) -> None:
    # Extract data from event payload
    reward_token_address = f'0x{event.payload.reward_token:x}'
    amount = event.payload.amount
    claimer_address = f'0x{event.payload.claimer:x}'
    unallocated_rewards = event.payload.unallocated_rewards
    block_timestamp = event.payload.block_timestamp

    # Get farm address from event data
    farm_address = event.data.from_address

    # Get farm from database
    farm = await models.Farm.get_or_none(address=farm_address)
    if not farm:
        ctx.logger.warning(f'Farm {farm_address} not found when claiming unallocated rewards')
        return

    # Update reward in the database if it exists
    reward = await models.Reward.get_or_none(address=reward_token_address, farm_address=farm_address)

    if reward:
        # Update unallocated rewards
        reward.unallocated_rewards = unallocated_rewards

        # Decrease remaining_amount when unallocated rewards are claimed
        reward.remaining_amount = str(int(reward.remaining_amount) - int(amount))

        reward.updated_at = block_timestamp
        await reward.save()

        # Create a reward event to track this claim
        transaction_hash = event.data.transaction_hash
        await models.RewardEvent.create(
            transaction_hash=transaction_hash,
            created_at=block_timestamp,
            event_type=models.RewardEventType.REWARD_ADDED,  # Using REWARD_ADDED as there's no specific type for unallocated claims
            agent_address=claimer_address,
            reward_token=reward_token_address,
            reward_amount=amount,
            reward_rate=None,
            reward_duration=None,
            period_finish=None,
            farm=farm,
        )

    ctx.logger.info(
        f'Unallocated rewards claimed: farm={farm_address}, token={reward_token_address}, '
        f'amount={amount}, claimer={claimer_address}, remaining={unallocated_rewards}'
    )
