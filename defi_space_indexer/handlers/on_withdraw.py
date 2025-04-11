from defi_space_indexer import models as models
from defi_space_indexer.types.farming_farm.starknet_events.withdraw import WithdrawPayload
from dipdup.context import HandlerContext
from dipdup.models.starknet import StarknetEvent


async def on_withdraw(
    ctx: HandlerContext,
    event: StarknetEvent[WithdrawPayload],
) -> None:
    # Extract data from event payload
    user_address = f'0x{event.payload.user_address:x}'
    staked_amount = event.payload.staked_amount
    penalty_amount = event.payload.penalty_amount
    total_staked = event.payload.total_staked
    user_staked = event.payload.user_staked
    penalty_end_time = event.payload.penalty_end_time
    block_timestamp = event.payload.block_timestamp
    
    # Get farm address and transaction hash from event data
    farm_address = event.data.from_address
    transaction_hash = event.data.transaction_hash
    
    # Get farm from database
    farm = await models.Farm.get_or_none(address=farm_address)
    if not farm:
        ctx.logger.warning(f"Farm {farm_address} not found when processing withdraw")
        return
    
    # Update farm total staked
    farm.total_staked = total_staked
    farm.updated_at = block_timestamp
    await farm.save()
    
    # Get user's stake
    agent_stake = await models.AgentStake.get_or_none(
        agent_address=user_address,
        farm_address=farm_address
    )
    
    if agent_stake:
        # Update agent's stake
        agent_stake.staked_amount = user_staked
        agent_stake.penalty_end_time = penalty_end_time
        agent_stake.updated_at = block_timestamp
        await agent_stake.save()
    else:
        ctx.logger.warning(
            f"AgentStake for agent {user_address} in farm {farm_address} not found when processing withdraw"
        )
    
    # Create agent stake event
    await models.AgentStakeEvent.create(
        transaction_hash=transaction_hash,
        created_at=block_timestamp,
        event_type=models.StakeEventType.WITHDRAW,
        agent_address=user_address,
        staked_amount=staked_amount,
        penalty_amount=penalty_amount,
        farm=farm,
        stake=agent_stake,
    )
    
    ctx.logger.info(
        f"Withdraw processed: agent={user_address}, farm={farm_address}, "
        f"amount={staked_amount}, penalty={penalty_amount}"
    )