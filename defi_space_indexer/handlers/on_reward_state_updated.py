from defi_space_indexer import models as models
from defi_space_indexer.types.farming_farm.starknet_events.reward_state_updated import RewardStateUpdatedPayload
from dipdup.context import HandlerContext
from dipdup.models.starknet import StarknetEvent


async def on_reward_state_updated(
    ctx: HandlerContext,
    event: StarknetEvent[RewardStateUpdatedPayload],
) -> None:
    # Extract data from event payload
    user_address = f'0x{event.payload.user_address:x}'
    reward_token_address = f'0x{event.payload.reward_token:x}'
    reward_per_token_paid = str(event.payload.reward_per_token_paid)  # Convert to string to handle large integers
    rewards = str(event.payload.rewards)  # Convert to string to handle large integers
    block_timestamp = event.payload.block_timestamp
    
    # Get farm address from event data
    farm_address = event.data.from_address
    
    # Get agent stake from database
    agent_stake = await models.AgentStake.get_or_none(
        farm_address=farm_address,
        agent_address=user_address
    )
    
    if not agent_stake:
        ctx.logger.warning(
            f"Agent stake not found for user {user_address} in farm {farm_address} "
            f"when updating reward state"
        )
        return
    
    # Update agent stake's reward state
    if not agent_stake.reward_per_token_paid:
        agent_stake.reward_per_token_paid = {}
    
    if not agent_stake.rewards:
        agent_stake.rewards = {}
    
    # Update reward state - matching the contract's storage structure
    agent_stake.reward_per_token_paid[reward_token_address] = reward_per_token_paid  # The user_reward_per_token_paid value
    agent_stake.rewards[reward_token_address] = rewards  # The previously accumulated rewards
    agent_stake.updated_at = block_timestamp
    
    await agent_stake.save()
    
    # Update or create RewardPerAgent record
    # First, get the reward for this token from the farm
    reward = await models.Reward.get_or_none(
        address=reward_token_address,
        farm_address=farm_address
    )
    
    if not reward:
        ctx.logger.warning(
            f"Reward not found for token {reward_token_address} in farm {farm_address} "
            f"when updating reward state for user {user_address}"
        )
        return
    
    # Get current reward_per_token_stored from reward model
    current_reward_per_token = reward.reward_per_token_stored
    
    # Get user's staked amount
    balance = agent_stake.staked_amount
    
    # Calculate total pending rewards using the contract's earned function logic
    total_last_pending_rewards = rewards  # Start with previously accumulated rewards
    
    # Only calculate additional rewards if user has a balance and reward_per_token has increased
    if balance != "0" and int(current_reward_per_token) > int(reward_per_token_paid):
        # Get token decimals for precision factor
        decimals = reward.decimals
        precision_factor = 10 ** decimals
        
        # Calculate new rewards: balance * (current_reward_per_token - user_reward_per_token_paid) / precision_factor
        new_rewards = (int(balance) * (int(current_reward_per_token) - int(reward_per_token_paid))) // precision_factor
        
        # Add new rewards to previously accumulated rewards
        total_last_pending_rewards = str(int(rewards) + new_rewards)
    
    # Try to get existing RewardPerAgent record
    reward_per_agent = await models.RewardPerAgent.get_or_none(
        agent_address=user_address,
        reward_token_address=reward_token_address,
        farm_address=farm_address
    )
    
    if not reward_per_agent:
        # Create new RewardPerAgent record if not exists
        reward_per_agent = await models.RewardPerAgent.create(
            agent_address=user_address,
            reward_token_address=reward_token_address,
            farm_address=farm_address,
            last_pending_rewards=total_last_pending_rewards,  # Store the total calculated rewards
            reward_per_token_paid=reward_per_token_paid,  # Store user_reward_per_token_paid
            created_at=block_timestamp,
            updated_at=block_timestamp,
            agent_stake=agent_stake,
            reward=reward
        )
    else:
        # Update existing RewardPerAgent record with calculated values
        reward_per_agent.last_pending_rewards = total_last_pending_rewards
        reward_per_agent.reward_per_token_paid = reward_per_token_paid
        reward_per_agent.updated_at = block_timestamp
        await reward_per_agent.save()
    
    ctx.logger.info(
        f"Reward state updated: user={user_address}, farm={farm_address}, "
        f"token={reward_token_address}, reward_per_token_paid={reward_per_token_paid}, "
        f"rewards={rewards}, total_pending={total_last_pending_rewards}"
    )