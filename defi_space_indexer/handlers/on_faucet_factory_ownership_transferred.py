from defi_space_indexer import models as models
from defi_space_indexer.types.faucet_factory.starknet_events.ownership_transferred import OwnershipTransferredPayload
from dipdup.context import HandlerContext
from dipdup.models.starknet import StarknetEvent


async def on_faucet_factory_ownership_transferred(
    ctx: HandlerContext,
    event: StarknetEvent[OwnershipTransferredPayload],
) -> None:
    # Extract data from the event
    factory_address = f'0x{event.payload.faucet_factory:x}'
    previous_owner = f'0x{event.payload.previous_owner:x}'
    new_owner = f'0x{event.payload.new_owner:x}'
    block_timestamp = event.payload.block_timestamp
    
    # Update the factory model
    factory = await models.FaucetFactory.get_or_none(address=factory_address)
    if not factory:
        ctx.logger.error(f"Factory {factory_address} not found when updating ownership from {previous_owner} to {new_owner}")
        return
        
    # Log the ownership change in the config history
    factory.config_history.append({
        'field': 'owner',
        'old_value': factory.owner,
        'new_value': new_owner,
        'timestamp': block_timestamp,
    })
    
    # Update the owner
    factory.owner = new_owner
    factory.updated_at = block_timestamp
    
    # Save the changes
    await factory.save()
        