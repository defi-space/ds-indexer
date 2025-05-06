from defi_space_indexer import models as models
from defi_space_indexer.types.farming_factory.starknet_events.config_updated import ConfigUpdatedPayload
from dipdup.context import HandlerContext
from dipdup.models.starknet import StarknetEvent


async def on_farm_factory_config_updated(
    ctx: HandlerContext,
    event: StarknetEvent[ConfigUpdatedPayload],
) -> None:
    # Extract data from event payload
    field_name = event.payload.field_name
    old_value = event.payload.old_value
    new_value = event.payload.new_value
    farm_factory_address = f'0x{event.payload.farm_factory:x}'
    block_timestamp = event.payload.block_timestamp
    
    # Get farm factory from database
    farm_factory = await models.FarmFactory.get_or_none(address=farm_factory_address)
    if not farm_factory:
        ctx.logger.warning(f"Farm factory {farm_factory_address} not found when updating config")
        return
    
    # Convert felt252 field_name to string for readability
    field_name_str = str(field_name)
    
    # Update the appropriate field in the FarmFactory model based on field_name
    if field_name_str == "owner":
        farm_factory.owner = f'0x{new_value:x}'
    elif field_name_str == "farm_class_hash":
        farm_factory.farm_class_hash = f'0x{new_value:x}'
    elif field_name_str == "game_session_id":
        # Use string representation for large integers to avoid overflow
        farm_factory.game_session_id = int(new_value)
    # Add other fields as needed
    
    # Update or initialize the config_history field
    if not farm_factory.config_history:
        farm_factory.config_history = []
    
    # Format values based on field type
    old_value_formatted = str(old_value)
    new_value_formatted = str(new_value)
    if field_name_str in ["owner", "farm_class_hash"]:
        old_value_formatted = f'0x{old_value:x}'
        new_value_formatted = f'0x{new_value:x}'
    
    # Add the change to config history
    farm_factory.config_history.append({
        'field': field_name_str,
        'old_value': old_value_formatted,
        'new_value': new_value_formatted,
        'timestamp': block_timestamp
    })
    
    # Update the timestamp
    farm_factory.updated_at = block_timestamp
    
    # Save the updated farm factory model
    await farm_factory.save()
    
    ctx.logger.info(
        f"Farm factory config updated: {farm_factory_address}, field={field_name_str}, "
        f"old_value={old_value_formatted}, new_value={new_value_formatted}"
    )