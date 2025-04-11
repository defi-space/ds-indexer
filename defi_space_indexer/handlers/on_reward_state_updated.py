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
    
    # Update reward state
    agent_stake.reward_per_token_paid[reward_token_address] = reward_per_token_paid  # Already a string
    agent_stake.rewards[reward_token_address] = rewards  # Already a string
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
    
    reward_per_agent, created = await models.RewardPerAgent.get_or_create(
        agent_address=user_address,
        reward_token_address=reward_token_address,
        farm_address=farm_address,
        defaults={
            'pending_rewards': rewards,  # Already a string
            'reward_per_token_paid': reward_per_token_paid,  # Already a string
            'created_at': block_timestamp,
            'updated_at': block_timestamp,
            'agent_stake': agent_stake,
            'reward': reward,
        }
    )
    
    if not created:
        reward_per_agent.pending_rewards = rewards  # Already a string
        reward_per_agent.reward_per_token_paid = reward_per_token_paid  # Already a string
        reward_per_agent.updated_at = block_timestamp
        reward_per_agent.reward = reward  # Ensure reward relationship is maintained
        await reward_per_agent.save()
    
    ctx.logger.info(
        f"Reward state updated: user={user_address}, farm={farm_address}, "
        f"token={reward_token_address}, reward_per_token_paid={reward_per_token_paid}, "
        f"rewards={rewards}"
    )