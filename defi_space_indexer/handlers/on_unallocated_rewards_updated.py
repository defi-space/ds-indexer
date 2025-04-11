from defi_space_indexer import models as models
from defi_space_indexer.types.farming_farm.starknet_events.unallocated_rewards_updated import UnallocatedRewardsUpdatedPayload
from dipdup.context import HandlerContext
from dipdup.models.starknet import StarknetEvent


async def on_unallocated_rewards_updated(
    ctx: HandlerContext,
    event: StarknetEvent[UnallocatedRewardsUpdatedPayload],
) -> None:
    # Extract data from event payload
    reward_token_address = f'0x{event.payload.reward_token:x}'
    previous_amount = event.payload.previous_amount
    new_amount = event.payload.new_amount
    block_timestamp = event.payload.block_timestamp
    
    # Get farm address from event data
    farm_address = event.data.from_address
    
    # Get farm from database
    farm = await models.Farm.get_or_none(address=farm_address)
    if not farm:
        ctx.logger.warning(f"Farm {farm_address} not found when updating unallocated rewards")
        return
    
    # Update reward in the database if it exists
    reward = await models.Reward.get_or_none(
        address=reward_token_address,
        farm_address=farm_address
    )
    
    if reward:
        # Update unallocated rewards
        reward.unallocated_rewards = new_amount
        reward.updated_at = block_timestamp
        await reward.save()
    
    ctx.logger.info(
        f"Unallocated rewards updated: farm={farm_address}, token={reward_token_address}, "
        f"previous_amount={previous_amount}, new_amount={new_amount}"
    )