from defi_space_indexer import models as models
from defi_space_indexer.types.game_factory.starknet_events.config_updated import ConfigUpdatedPayload
from dipdup.context import HandlerContext
from dipdup.models.starknet import StarknetEvent


async def on_game_factory_config_updated(
    ctx: HandlerContext,
    event: StarknetEvent[ConfigUpdatedPayload],
) -> None:
    # Extract data from event payload
    field_name = event.payload.field_name
    old_value = event.payload.old_value
    new_value = event.payload.new_value
    factory_address = f'0x{event.payload.factory_address:x}'
    block_timestamp = event.payload.block_timestamp
    
    # Get game factory from database
    factory = await models.GameFactory.get_or_none(address=factory_address)
    if not factory:
        ctx.logger.warning(f"Game factory {factory_address} not found when updating config")
        return
    
    # Convert felt252 field_name to string for readability
    field_name_str = str(field_name)
    
    # Update the appropriate field in the GameFactory model based on field_name
    if field_name_str == "owner":
        factory.owner = f'0x{new_value:x}'
    elif field_name_str == "game_session_class_hash":
        factory.game_session_class_hash = f'0x{new_value:x}'
    # Add other fields as needed
    
    # Update or initialize the config_history field
    if not factory.config_history:
        factory.config_history = []
    
    # Format values based on field type
    old_value_formatted = str(old_value)  # Convert to string to avoid integer overflow
    new_value_formatted = str(new_value)  # Convert to string to avoid integer overflow
    if field_name_str in ["owner", "game_session_class_hash"]:
        old_value_formatted = f'0x{old_value:x}'
        new_value_formatted = f'0x{new_value:x}'
    
    # Add the change to config history
    factory.config_history.append({
        'field': field_name_str,
        'old_value': old_value_formatted,
        'new_value': new_value_formatted,
        'timestamp': block_timestamp
    })
    
    # Update the timestamp
    factory.updated_at = block_timestamp
    
    # Save the updated factory model
    await factory.save()
    
    ctx.logger.info(
        f"Game factory config updated: {factory_address}, field={field_name_str}, "
        f"old_value={old_value_formatted}, new_value={new_value_formatted}"
    )