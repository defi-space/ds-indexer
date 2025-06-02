from defi_space_indexer import models as models
from defi_space_indexer.types.farming_farm.starknet_events.reward_added import RewardAddedPayload
from dipdup.context import HandlerContext
from dipdup.models.starknet import StarknetEvent
from decimal import Decimal
from defi_space_indexer.utils import get_token_info


async def on_reward_added(
    ctx: HandlerContext,
    event: StarknetEvent[RewardAddedPayload],
) -> None:
    # Extract data from event payload
    reward_token = f'0x{event.payload.reward_token:x}'
    reward_amount = event.payload.reward_amount
    reward_duration = event.payload.reward_duration
    reward_rate = event.payload.reward_rate
    reward_per_token_stored = event.payload.reward_per_token_stored
    period_finish = event.payload.period_finish
    unallocated_rewards = event.payload.unallocated_rewards
    token_decimals = event.payload.token_decimals
    
    # Convert large integers to strings to avoid 64-bit range limitations
    reward_amount_str = str(reward_amount)
    reward_rate_str = str(reward_rate)
    reward_per_token_stored_str = str(reward_per_token_stored)
    period_finish_str = str(period_finish)
    unallocated_rewards_str = str(unallocated_rewards)
    
    # Get farm address from event data
    farm_address = event.data.from_address
    transaction_hash = event.data.transaction_hash
    block_timestamp = event.payload.block_timestamp
    
    # Get farm from database
    farm = await models.Farm.get_or_none(address=farm_address)
    if not farm:
        ctx.logger.warning(f"Farm {farm_address} not found when processing reward added event")
        return
    
    # Fetch token name, symbol, and decimals
    token_name, token_symbol, token_decimals = await get_token_info(reward_token)
    
    # Get or create Reward model
    reward, created = await models.Reward.get_or_create(
        address=reward_token,
        farm_address=farm_address,
        defaults={
            'initial_amount': reward_amount_str,
            'unallocated_rewards': unallocated_rewards_str,
            'remaining_amount': reward_amount_str,
            'rewards_duration': reward_duration,
            'period_finish': period_finish_str,
            'reward_rate': reward_rate_str,
            'game_session_id' : farm.game_session_id,
            'last_update_time': block_timestamp,
            'reward_per_token_stored': reward_per_token_stored_str,
            'reward_token_symbol': token_symbol,
            'reward_token_name': token_name,
            'decimals': token_decimals,
            'created_at': block_timestamp,
            'updated_at': block_timestamp,
            'farm': farm,
        }
    )
    
    if not created:
        # Update reward data
        reward.initial_amount = reward_amount_str
        reward.unallocated_rewards = unallocated_rewards_str
        reward.remaining_amount = reward_amount_str
        reward.rewards_duration = reward_duration
        reward.period_finish = period_finish_str
        reward.reward_rate = reward_rate_str
        reward.game_session_id = farm.game_session_id
        reward.last_update_time = block_timestamp
        reward.reward_per_token_stored = reward_per_token_stored_str
        reward.reward_token_symbol = token_symbol
        reward.reward_token_name = token_name
        reward.decimals = token_decimals
        reward.updated_at = block_timestamp
        await reward.save()
    else: 
        reward.initial_amount = reward_amount_str
        reward.remaining_amount = reward.remaining_amount + reward_amount_str
        reward.unallocated_rewards = unallocated_rewards_str
        reward.rewards_duration = reward_duration
        reward.period_finish = period_finish_str
        reward.reward_rate = reward_rate_str
        reward.game_session_id = farm.game_session_id
        reward.last_update_time = block_timestamp
        reward.reward_per_token_stored = reward_per_token_stored_str
        reward.reward_token_symbol = token_symbol
        reward.reward_token_name = token_name
        reward.decimals = token_decimals
        reward.updated_at = block_timestamp
        await reward.save()
    farm_active_rewards = farm.active_rewards or {}
    farm_active_rewards[reward_token] = {
        'rate': reward_rate_str,
        'duration': reward_duration,
        'finish': period_finish_str,
        'stored': reward_per_token_stored_str
    }
    farm.active_rewards = farm_active_rewards

    # Update farm reward tokens list if not already in it
    if reward_token not in farm.reward_tokens:
        farm.reward_tokens.append(reward_token)
    
    farm.updated_at = block_timestamp
    await farm.save()
    
    # Create reward event
    await models.RewardEvent.create(
        transaction_hash=transaction_hash,
        created_at=block_timestamp,
        event_type=models.RewardEventType.REWARD_ADDED,
        agent_address=None,  # No specific agent for reward addition
        reward_token=reward_token,
        reward_amount=reward_amount_str,
        reward_rate=reward_rate_str,
        reward_duration=reward_duration,
        period_finish=period_finish_str,
        farm=farm,
    )
    
    ctx.logger.info(
        f"Reward added to farm: farm={farm_address}, token={reward_token} ({token_symbol}), "
        f"amount={reward_amount}, rate={reward_rate}, duration={reward_duration}, "
        f"finish={period_finish}, decimals={token_decimals}"
    )