from defi_space_indexer import models as models
from defi_space_indexer.types.farming_farm.starknet_events.rewarder_added import RewarderAddedPayload
from dipdup.context import HandlerContext
from dipdup.models.starknet import StarknetEvent


async def on_rewarder_added(
    ctx: HandlerContext,
    event: StarknetEvent[RewarderAddedPayload],
) -> None:
    # Extract data from event payload
    rewarder_address = f'0x{event.payload.rewarder:x}'
    block_timestamp = event.payload.block_timestamp
    
    # Get farm address from event data
    farm_address = event.data.from_address
    
    # Get farm from database
    farm = await models.Farm.get_or_none(address=farm_address)
    if not farm:
        ctx.logger.warning(f"Farm {farm_address} not found when adding rewarder")
        return
    
    # Update farm's authorized rewarders list
    if not farm.authorized_rewarders:
        farm.authorized_rewarders = []
    
    if rewarder_address not in farm.authorized_rewarders:
        farm.authorized_rewarders.append(rewarder_address)
    
    farm.updated_at = block_timestamp
    await farm.save()
    
    # Create or update Rewarder model
    rewarder, created = await models.Rewarder.get_or_create(
        address=rewarder_address,
        farm_address=farm_address,
        defaults={
            'is_authorized': True,
            'created_at': block_timestamp,
            'updated_at': block_timestamp,
            'farm': farm,
        }
    )
    
    if not created:
        rewarder.is_authorized = True
        rewarder.updated_at = block_timestamp
        await rewarder.save()
    
    ctx.logger.info(
        f"Rewarder added: farm={farm_address}, rewarder={rewarder_address}"
    )