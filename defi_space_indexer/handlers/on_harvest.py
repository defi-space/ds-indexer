from defi_space_indexer import models as models
from defi_space_indexer.types.farming_farm.starknet_events.harvest import HarvestPayload
from dipdup.context import HandlerContext
from dipdup.models.starknet import StarknetEvent


async def on_harvest(
    ctx: HandlerContext,
    event: StarknetEvent[HarvestPayload],
) -> None:
    # Extract data from event payload
    user_address = f'0x{event.payload.user_address:x}'
    reward_token_address = f'0x{event.payload.reward_token:x}'
    reward_amount = str(event.payload.reward_amount)  # Convert to string to avoid overflow
    total_staked = str(event.payload.total_staked)  # Convert to string to avoid overflow
    user_staked = str(event.payload.user_staked)  # Convert to string to avoid overflow
    reward_per_token_stored = str(event.payload.reward_per_token_stored)  # Convert to string to avoid overflow
    block_timestamp = event.payload.block_timestamp
    
    # Get farm address and transaction hash from event data
    farm_address = event.data.from_address
    transaction_hash = event.data.transaction_hash
    
    # Get farm from database
    farm = await models.Farm.get_or_none(address=farm_address)
    if not farm:
        ctx.logger.warning(f"Farm {farm_address} not found when processing harvest event")
        return
    
    # Update farm total staked
    farm.total_staked = total_staked
    farm.updated_at = block_timestamp
    
    # Update or create reward token state in the farm
    if not farm.active_rewards:
        farm.active_rewards = {}
    
    # Create or update reward token state
    reward_token_state = farm.active_rewards.get(reward_token_address, {})
    reward_token_state['stored'] = reward_per_token_stored
    farm.active_rewards[reward_token_address] = reward_token_state
    
    await farm.save()
    
    # Get or create agent stake
    agent_stake = await models.AgentStake.get_or_none(
        farm_address=farm_address,
        agent_address=user_address
    )
    
    if agent_stake:
        # Update agent stake amount
        agent_stake.staked_amount = user_staked
        agent_stake.updated_at = block_timestamp
        
        # Update reward per token paid
        if not agent_stake.reward_per_token_paid:
            agent_stake.reward_per_token_paid = {}
        agent_stake.reward_per_token_paid[reward_token_address] = reward_per_token_stored
        
        # Update rewards
        if not agent_stake.rewards:
            agent_stake.rewards = {}
        # Reset harvested reward amount to 0
        agent_stake.rewards[reward_token_address] = 0
        
        await agent_stake.save()
    
    # Get reward info
    reward = await models.Reward.get_or_none(
        address=reward_token_address,
        farm_address=farm_address
    )
    
    # If there's no reward for this token, log a warning
    if not reward:
        ctx.logger.warning(
            f"Reward not found for token {reward_token_address} in farm {farm_address} "
            f"when processing harvest event"
        )
    
    # Create reward event
    await models.RewardEvent.create(
        transaction_hash=transaction_hash,
        created_at=block_timestamp,
        event_type=models.RewardEventType.HARVEST,
        agent_address=user_address,
        reward_token=reward_token_address,
        reward_amount=reward_amount,
        # Set these fields to null for harvest events
        reward_rate=None,
        reward_duration=None,
        period_finish=None,
        farm=farm,
    )
    
    ctx.logger.info(
        f"Harvest event processed: user={user_address}, farm={farm_address}, "
        f"token={reward_token_address}, amount={reward_amount}"
    )