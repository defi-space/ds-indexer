from defi_space_indexer import models as models
from defi_space_indexer.types.farming_farm.starknet_events.ownership_transferred import OwnershipTransferredPayload
from dipdup.context import HandlerContext
from dipdup.models.starknet import StarknetEvent


async def on_farm_ownership_transferred(
    ctx: HandlerContext,
    event: StarknetEvent[OwnershipTransferredPayload],
) -> None:
    # Extract data from event payload
    previous_owner = f'0x{event.payload.previous_owner:x}'
    new_owner = f'0x{event.payload.new_owner:x}'
    block_timestamp = event.payload.block_timestamp
    
    # Get farm address from event data
    farm_address = event.data.from_address
    
    # Get farm from database
    farm = await models.Farm.get_or_none(address=farm_address)
    if not farm:
        ctx.logger.warning(f"Farm {farm_address} not found when transferring ownership")
        return
    
    # Update the farm owner
    farm.owner = new_owner
    farm.updated_at = block_timestamp
    
    # Update or initialize the config_history field
    if not farm.config_history:
        farm.config_history = []
    
    # Add the ownership change to config history
    farm.config_history.append({
        'field': 'owner',
        'old_value': previous_owner,
        'new_value': new_owner,
        'timestamp': block_timestamp
    })
    
    # Save the changes
    await farm.save()
    
    ctx.logger.info(
        f"Farm ownership transferred: farm={farm_address}, "
        f"previous_owner={previous_owner}, new_owner={new_owner}"
    )