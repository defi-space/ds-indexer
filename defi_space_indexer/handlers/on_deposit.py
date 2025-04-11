from defi_space_indexer import models as models
from defi_space_indexer.types.farming_farm.starknet_events.deposit import DepositPayload
from dipdup.context import HandlerContext
from dipdup.models.starknet import StarknetEvent


async def on_deposit(
    ctx: HandlerContext,
    event: StarknetEvent[DepositPayload],
) -> None:
    # Extract data from event payload
    user_address = f'0x{event.payload.user_address:x}'
    staked_amount = event.payload.staked_amount
    total_staked = event.payload.total_staked
    user_staked = event.payload.user_staked
    multiplier = event.payload.multiplier
    penalty_end_time = event.payload.penalty_end_time
    block_timestamp = event.payload.block_timestamp
    
    # Get farm address from event data
    farm_address = event.data.from_address
    transaction_hash = event.data.transaction_hash
    
    # Get farm from database
    farm = await models.Farm.get_or_none(address=farm_address)
    if not farm:
        ctx.logger.warning(f"Farm {farm_address} not found when processing deposit event")
        return
    
    # Update farm total staked and multiplier
    farm.total_staked = total_staked
    farm.multiplier = multiplier
    farm.updated_at = block_timestamp
    await farm.save()
    
    # Get or create agent stake
    agent_stake, created = await models.AgentStake.get_or_create(
        farm_address=farm_address,
        agent_address=user_address,
        defaults={
            'staked_amount': 0,
            'penalty_end_time': 0,
            'reward_per_token_paid': {},
            'rewards': {},
            'created_at': block_timestamp,
            'updated_at': block_timestamp,
            'farm': farm,
        }
    )
    
    # Update agent stake
    agent_stake.staked_amount = user_staked
    agent_stake.penalty_end_time = penalty_end_time
    agent_stake.updated_at = block_timestamp
    await agent_stake.save()
    
    # Create agent stake event
    await models.AgentStakeEvent.create(
        transaction_hash=transaction_hash,
        created_at=block_timestamp,
        event_type=models.StakeEventType.DEPOSIT,
        agent_address=user_address,
        staked_amount=staked_amount,
        farm=farm,
        stake=agent_stake
    )
    
    ctx.logger.info(
        f"Deposit event processed: agent={user_address}, farm={farm_address}, "
        f"amount={staked_amount}, total_staked={total_staked}, user_staked={user_staked}"
    )