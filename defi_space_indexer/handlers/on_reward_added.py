from defi_space_indexer import models as models
from defi_space_indexer.types.farming_farm.starknet_events.reward_added import RewardAddedPayload
from dipdup.context import HandlerContext
from dipdup.models.starknet import StarknetEvent
from decimal import Decimal


async def on_reward_added(
    ctx: HandlerContext,
    event: StarknetEvent[RewardAddedPayload],
) -> None:
    # Extract data from event payload
    reward_token_address = f'0x{event.payload.reward_token:x}'
    reward_amount = str(event.payload.reward_amount)  # Convert to string to avoid overflow
    reward_rate = str(event.payload.reward_rate)  # Convert to string to avoid overflow
    reward_duration = str(event.payload.reward_duration)  # Convert to string to avoid overflow
    period_finish = str(event.payload.period_finish)  # Convert to string to avoid overflow
    reward_per_token_stored = str(event.payload.reward_per_token_stored)  # Convert to string to avoid overflow
    unallocated_rewards = str(event.payload.unallocated_rewards)  # Convert to string to avoid overflow
    token_decimals = event.payload.token_decimals
    block_timestamp = event.payload.block_timestamp
    rewarder_address = f'0x{event.payload.rewarder:x}'
    
    # Get farm address and transaction hash from event data
    farm_address = event.data.from_address
    transaction_hash = event.data.transaction_hash
    
    # Get farm from database
    farm = await models.Farm.get_or_none(address=farm_address)
    if not farm:
        ctx.logger.warning(f"Farm {farm_address} not found when adding reward")
        return
    
    # Update farm with new reward token if needed
    if reward_token_address not in farm.reward_tokens:
        farm.reward_tokens.append(reward_token_address)
    
    # Update or create reward token state in the farm
    if not farm.active_rewards:
        farm.active_rewards = {}
    
    # Update reward token state
    farm.active_rewards[reward_token_address] = {
        'rate': reward_rate,
        'duration': reward_duration,
        'finish': period_finish,
        'stored': reward_per_token_stored
    }
    
    farm.updated_at = block_timestamp
    await farm.save()
    
    # Get or create Reward model
    reward, created = await models.Reward.get_or_create(
        address=reward_token_address,
        farm_address=farm_address,
        defaults={
            'unallocated_rewards': unallocated_rewards,
            'rewards_duration': reward_duration,
            'period_finish': period_finish,
            'reward_rate': reward_rate,
            'last_update_time': block_timestamp,
            'reward_per_token_stored': reward_per_token_stored,
            'decimals': token_decimals,
            'created_at': block_timestamp,
            'updated_at': block_timestamp,
            'farm': farm,
        }
    )
    
    if not created:
        # Update existing reward
        reward.unallocated_rewards = unallocated_rewards
        reward.rewards_duration = reward_duration
        reward.period_finish = period_finish
        reward.reward_rate = reward_rate
        reward.reward_per_token_stored = reward_per_token_stored
        reward.last_update_time = block_timestamp
        reward.updated_at = block_timestamp
        await reward.save()
        
        # Update all RewardPerAgent records that refer to this reward
        reward_per_agents = await models.RewardPerAgent.filter(
            reward_token_address=reward_token_address,
            farm_address=farm_address
        )
        
        for rpa in reward_per_agents:
            rpa.reward = reward
            rpa.updated_at = block_timestamp
            await rpa.save()
    
    # Create reward event
    await models.RewardEvent.create(
        transaction_hash=transaction_hash,
        created_at=block_timestamp,
        event_type=models.RewardEventType.REWARD_ADDED,
        agent_address=None,  # Not applicable for reward additions
        reward_token=reward_token_address,
        reward_amount=reward_amount,
        reward_rate=reward_rate,
        reward_duration=reward_duration,
        period_finish=period_finish,
        farm=farm,
    )
    
    ctx.logger.info(
        f"Reward added: farm={farm_address}, token={reward_token_address}, "
        f"amount={reward_amount}, rate={reward_rate}, duration={reward_duration}, "
        f"finish={period_finish}, rewarder={rewarder_address}"
    )