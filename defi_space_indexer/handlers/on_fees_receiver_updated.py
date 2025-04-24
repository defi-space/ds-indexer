from defi_space_indexer import models as models
from defi_space_indexer.types.amm_factory.starknet_events.fees_receiver_updated import FeesReceiverUpdatedPayload
from dipdup.context import HandlerContext
from dipdup.models.starknet import StarknetEvent


async def on_fees_receiver_updated(
    ctx: HandlerContext,
    event: StarknetEvent[FeesReceiverUpdatedPayload],
) -> None:
    # Extract data from event payload
    previous_fee_to = f'0x{event.payload.previous_fee_to:x}'
    new_fee_to = f'0x{event.payload.new_fee_to:x}'
    factory_address = f'0x{event.payload.factory_address:x}'
    block_timestamp = event.payload.block_timestamp
    
    # Get factory from database
    factory = await models.AmmFactory.get_or_none(address=factory_address)
    if not factory:
        ctx.logger.warning(f"AmmFactory {factory_address} not found when updating fees receiver")
        return
    
    # Update the factory fee_to field
    factory.fee_to = new_fee_to
    factory.updated_at = block_timestamp
    
    # Update or initialize the config_history field
    if not factory.config_history:
        factory.config_history = []
    
    # Add the fee receiver change to config history
    factory.config_history.append({
        'field': 'fee_to',
        'old_value': previous_fee_to,
        'new_value': new_fee_to,
        'timestamp': block_timestamp
    })
    
    # Save the changes
    await factory.save()
    
    ctx.logger.info(
        f"AmmFactory fees receiver updated: factory={factory_address}, "
        f"previous_fee_to={previous_fee_to}, new_fee_to={new_fee_to}"
    )