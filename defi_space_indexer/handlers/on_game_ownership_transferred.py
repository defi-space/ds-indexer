from defi_space_indexer import models as models
from defi_space_indexer.types.game_factory.starknet_events.ownership_transferred import OwnershipTransferredPayload
from dipdup.context import HandlerContext
from dipdup.models.starknet import StarknetEvent


async def on_game_ownership_transferred(
    ctx: HandlerContext,
    event: StarknetEvent[OwnershipTransferredPayload],
) -> None:
    # Extract data from event payload
    previous_owner = f'0x{event.payload.previous_owner:x}'
    new_owner = f'0x{event.payload.new_owner:x}'
    factory_address = f'0x{event.payload.factory_address:x}'
    block_timestamp = event.payload.block_timestamp
    
    # Get game factory from database
    factory = await models.GameFactory.get_or_none(address=factory_address)
    if not factory:
        ctx.logger.warning(f"Game factory {factory_address} not found when transferring ownership")
        return
    
    # Update the game factory owner
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
        f"Game factory ownership transferred: factory={factory_address}, "
        f"previous_owner={previous_owner}, new_owner={new_owner}"
    )