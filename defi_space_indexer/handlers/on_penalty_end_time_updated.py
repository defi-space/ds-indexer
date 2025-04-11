from defi_space_indexer import models as models
from defi_space_indexer.types.farming_farm.starknet_events.penalty_end_time_updated import PenaltyEndTimeUpdatedPayload
from dipdup.context import HandlerContext
from dipdup.models.starknet import StarknetEvent


async def on_penalty_end_time_updated(
    ctx: HandlerContext,
    event: StarknetEvent[PenaltyEndTimeUpdatedPayload],
) -> None:
    # Extract data from event payload
    user_address = f'0x{event.payload.user_address:x}'
    old_end_time = event.payload.old_end_time
    new_end_time = event.payload.new_end_time
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
            f"when updating penalty end time"
        )
        return
    
    # Update the agent stake
    agent_stake.penalty_end_time = new_end_time
    agent_stake.updated_at = block_timestamp
    await agent_stake.save()
    
    ctx.logger.info(
        f"Penalty end time updated: user={user_address}, farm={farm_address}, "
        f"old_end_time={old_end_time}, new_end_time={new_end_time}"
    )