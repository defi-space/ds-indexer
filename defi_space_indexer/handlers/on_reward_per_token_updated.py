from defi_space_indexer import models as models
from defi_space_indexer.types.farming_farm.starknet_events.reward_per_token_updated import RewardPerTokenUpdatedPayload
from dipdup.context import HandlerContext
from dipdup.models.starknet import StarknetEvent


async def on_reward_per_token_updated(
    ctx: HandlerContext,
    event: StarknetEvent[RewardPerTokenUpdatedPayload],
) -> None:
    # Extract data from event payload
    reward_token_address = f'0x{event.payload.reward_token:x}'
    previous_value = event.payload.previous_value
    new_value = event.payload.new_value
    block_timestamp = event.payload.block_timestamp
    
    # Get farm address from event data
    farm_address = event.data.from_address
    
    # Get farm from database
    farm = await models.Farm.get_or_none(address=farm_address)
    if not farm:
        ctx.logger.warning(f"Farm {farm_address} not found when updating reward per token")
        return
    
    # Update farm's active_rewards with new reward per token stored
    if not farm.active_rewards:
        farm.active_rewards = {}
    
    # Get existing reward token state or create new one
    reward_token_state = farm.active_rewards.get(reward_token_address, {})
    reward_token_state['stored'] = new_value
    farm.active_rewards[reward_token_address] = reward_token_state
    
    farm.updated_at = block_timestamp
    await farm.save()
    
    # Update Reward model if it exists
    reward = await models.Reward.get_or_none(
        address=reward_token_address,
        farm_address=farm_address
    )
    
    if reward:
        reward.reward_per_token_stored = new_value
        reward.last_update_time = block_timestamp
        reward.updated_at = block_timestamp
        await reward.save()
    
    ctx.logger.info(
        f"Reward per token updated: farm={farm_address}, token={reward_token_address}, "
        f"previous_value={previous_value}, new_value={new_value}"
    )