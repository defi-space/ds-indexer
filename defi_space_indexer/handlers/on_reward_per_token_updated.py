from dipdup.context import HandlerContext
from dipdup.models.starknet import StarknetEvent

from defi_space_indexer import models as models
from defi_space_indexer.types.farming_farm.starknet_events.reward_per_token_updated import RewardPerTokenUpdatedPayload


async def on_reward_per_token_updated(
    ctx: HandlerContext,
    event: StarknetEvent[RewardPerTokenUpdatedPayload],
) -> None:
    # Extract data from event payload
    reward_token_address = f'0x{event.payload.reward_token:x}'
    previous_value = str(event.payload.previous_value)  # Convert to string to handle large integers
    new_value = str(event.payload.new_value)  # Convert to string to handle large integers
    block_timestamp = event.payload.block_timestamp

    # Get farm address from event data
    farm_address = event.data.from_address

    # Get farm from database
    farm = await models.Farm.get_or_none(address=farm_address)
    if not farm:
        ctx.logger.warning(f'Farm {farm_address} not found when updating reward per token')
        return

    # Update farm's active_rewards with new reward per token stored
    if not farm.active_rewards:
        farm.active_rewards = {}

    # Get existing reward token state or create new one
    reward_token_state = farm.active_rewards.get(reward_token_address, {})
    reward_token_state['stored'] = new_value  # Already a string
    farm.active_rewards[reward_token_address] = reward_token_state

    farm.updated_at = block_timestamp
    await farm.save()

    # Update Reward model if it exists
    reward = await models.Reward.get_or_none(address=reward_token_address, farm_address=farm_address)

    if reward:
        reward.reward_per_token_stored = new_value  # Already a string
        reward.last_update_time = block_timestamp
        reward.updated_at = block_timestamp
        await reward.save()

        # Get token decimals for precision factor
        decimals = reward.decimals
        precision_factor = 10**decimals

        # Get all agent stakes for this farm
        agent_stakes = await models.AgentStake.filter(farm_address=farm_address)

        # Update pending rewards for all agent stakes
        for agent_stake in agent_stakes:
            # Only process agents that have a balance
            if agent_stake.staked_amount == '0':
                continue

            # Get the agent's reward per token paid
            if not agent_stake.reward_per_token_paid or reward_token_address not in agent_stake.reward_per_token_paid:
                continue

            user_reward_per_token_paid = agent_stake.reward_per_token_paid[reward_token_address]

            # Get the agent's accumulated rewards
            previous_rewards = '0'
            if agent_stake.rewards and reward_token_address in agent_stake.rewards:
                previous_rewards = agent_stake.rewards[reward_token_address]

            # Get or create the RewardPerAgent record
            reward_per_agent = await models.RewardPerAgent.get_or_none(
                agent_address=agent_stake.agent_address,
                reward_token_address=reward_token_address,
                farm_address=farm_address,
            )

            if reward_per_agent:
                # Calculate new pending rewards using contract's earned function logic
                if int(new_value) > int(user_reward_per_token_paid):
                    # Calculate new rewards: balance * (current_reward_per_token - user_reward_per_token_paid) / precision_factor
                    new_rewards = (
                        int(agent_stake.staked_amount) * (int(new_value) - int(user_reward_per_token_paid))
                    ) // precision_factor

                    # Add new rewards to previously accumulated rewards
                    total_last_pending_rewards = str(int(previous_rewards) + new_rewards)

                    # Update the RewardPerAgent record
                    reward_per_agent.last_pending_rewards = total_last_pending_rewards
                    reward_per_agent.updated_at = block_timestamp
                    await reward_per_agent.save()

    ctx.logger.info(
        f'Reward per token updated: farm={farm_address}, token={reward_token_address}, '
        f'previous_value={previous_value}, new_value={new_value}'
    )
