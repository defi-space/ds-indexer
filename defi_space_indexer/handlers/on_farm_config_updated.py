from defi_space_indexer import models as models
from defi_space_indexer.types.farming_farm.starknet_events.config_updated import ConfigUpdatedPayload
from dipdup.context import HandlerContext
from dipdup.models.starknet import StarknetEvent
from decimal import Decimal


async def on_farm_config_updated(
    ctx: HandlerContext,
    event: StarknetEvent[ConfigUpdatedPayload],
) -> None:
    # Extract data from event payload
    field_name = event.payload.field_name
    old_value = event.payload.old_value
    new_value = event.payload.new_value
    farm_address = event.data.from_address  # The contract address emitting the event
    block_timestamp = event.payload.block_timestamp
    
    # Convert felt252 field_name to string for readability
    field_name_str = str(field_name)
    
    # Get farm from database
    farm = await models.Farm.get_or_none(address=farm_address)
    if not farm:
        ctx.logger.warning(f"Farm {farm_address} not found when updating config")
        return
    
    # Update the appropriate field in the Farm model based on field_name
    if field_name_str == "locked":
        farm.locked = bool(new_value)
    elif field_name_str == "multiplier":
        # Use string representation for large integers to avoid overflow
        farm.multiplier = str(new_value)
    elif field_name_str == "penalty_duration":
        # Use string representation for large integers to avoid overflow
        farm.penalty_duration = str(new_value)
    elif field_name_str == "withdraw_penalty":
        # Use string representation for large integers to avoid overflow
        farm.withdraw_penalty = str(new_value)
    elif field_name_str == "penalty_receiver":
        farm.penalty_receiver = f'0x{new_value:x}'
    elif field_name_str == "game_session_id":
        # Use string representation for large integers to avoid overflow
        farm.game_session_id = str(new_value)
    # Add other fields as needed
    
    # Update or initialize the config_history field
    if not farm.config_history:
        farm.config_history = []
    
    # Format values based on field type
    old_value_formatted = str(old_value)
    new_value_formatted = str(new_value)
    if field_name_str in ["penalty_receiver"]:
        old_value_formatted = f'0x{old_value:x}'
        new_value_formatted = f'0x{new_value:x}'
    
    # Add the change to config history
    farm.config_history.append({
        'field': field_name_str,
        'old_value': old_value_formatted,
        'new_value': new_value_formatted,
        'timestamp': block_timestamp
    })
    
    # Update the timestamp
    farm.updated_at = block_timestamp
    
    # Save the updated farm model
    await farm.save()
    
    ctx.logger.info(
        f"Farm config updated: {farm_address}, field={field_name_str}, "
        f"old_value={old_value_formatted}, new_value={new_value_formatted}"
    )