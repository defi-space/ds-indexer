from defi_space_indexer import models as models
from defi_space_indexer.types.farming_farm.starknet_events.rewarder_removed import RewarderRemovedPayload
from dipdup.context import HandlerContext
from dipdup.models.starknet import StarknetEvent


async def on_rewarder_removed(
    ctx: HandlerContext,
    event: StarknetEvent[RewarderRemovedPayload],
) -> None:
    # Extract data from event payload
    rewarder_address = f'0x{event.payload.rewarder:x}'
    block_timestamp = event.payload.block_timestamp
    
    # Get farm address from event data
    farm_address = event.data.from_address
    
    # Get farm from database
    farm = await models.Farm.get_or_none(address=farm_address)
    if not farm:
        ctx.logger.warning(f"Farm {farm_address} not found when removing rewarder")
        return
    
    # Update farm's authorized rewarders list
    if farm.authorized_rewarders and rewarder_address in farm.authorized_rewarders:
        farm.authorized_rewarders.remove(rewarder_address)
    
    farm.updated_at = block_timestamp
    await farm.save()
    
    # Update Rewarder model if it exists
    rewarder = await models.Rewarder.get_or_none(
        address=rewarder_address,
        farm_address=farm_address
    )
    
    if rewarder:
        rewarder.is_authorized = False
        rewarder.updated_at = block_timestamp
        await rewarder.save()
    
    ctx.logger.info(
        f"Rewarder removed: farm={farm_address}, rewarder={rewarder_address}"
    )