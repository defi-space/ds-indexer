from defi_space_indexer import models as models
from defi_space_indexer.types.amm_factory.starknet_events.owner_updated import OwnerUpdatedPayload
from dipdup.context import HandlerContext
from dipdup.models.starknet import StarknetEvent


async def on_owner_updated(
    ctx: HandlerContext,
    event: StarknetEvent[OwnerUpdatedPayload],
) -> None:
    # Extract data from event payload
    previous_owner = f'0x{event.payload.previous_owner:x}'
    new_owner = f'0x{event.payload.new_owner:x}'
    factory_address = f'0x{event.payload.factory_address:x}'
    block_timestamp = event.payload.block_timestamp
    
    # Get factory from database
    factory = await models.Factory.get_or_none(address=factory_address)
    if not factory:
        ctx.logger.warning(f"Factory {factory_address} not found when updating owner")
        return
    
    # Update the factory owner
    factory.owner = new_owner
    factory.updated_at = block_timestamp
    
    # Update or initialize the config_history field
    if not factory.config_history:
        factory.config_history = []
    
    # Add the ownership change to config history
    factory.config_history.append({
        'field': 'owner',
        'old_value': previous_owner,
        'new_value': new_owner,
        'timestamp': block_timestamp
    })
    
    # Save the changes
    await factory.save()
    
    ctx.logger.info(
        f"Factory owner updated: factory={factory_address}, "
        f"previous_owner={previous_owner}, new_owner={new_owner}"
    )