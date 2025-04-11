from defi_space_indexer import models as models
from defi_space_indexer.types.game_session.starknet_events.config_updated import ConfigUpdatedPayload
from dipdup.context import HandlerContext
from dipdup.models.starknet import StarknetEvent


async def on_game_config_updated(
    ctx: HandlerContext,
    event: StarknetEvent[ConfigUpdatedPayload],
) -> None:
    # Extract data from event payload
    field_name = event.payload.field_name
    old_value = event.payload.old_value
    new_value = event.payload.new_value
    session_address = f'0x{event.payload.session_address:x}'
    block_timestamp = event.payload.block_timestamp
    
    # Get game session from database
    session = await models.GameSession.get_or_none(address=session_address)
    if not session:
        ctx.logger.warning(f"Game session {session_address} not found when updating config")
        return
    
    # Convert felt252 field_name to string for readability
    field_name_str = str(field_name)
    
    # Update the appropriate field in the GameSession model based on field_name
    if field_name_str == "burn_fee_percentage":
        session.burn_fee_percentage = int(new_value)
    elif field_name_str == "platform_fee_percentage":
        session.platform_fee_percentage = int(new_value)
    elif field_name_str == "fee_recipient":
        session.fee_recipient = f'0x{new_value:x}'
    # Add other fields as needed
    
    # Update or initialize the config_history field
    if not session.config_history:
        session.config_history = []
    
    # Format values based on field type
    old_value_formatted = old_value
    new_value_formatted = new_value
    if field_name_str in ["fee_recipient"]:
        old_value_formatted = f'0x{old_value:x}'
        new_value_formatted = f'0x{new_value:x}'
    
    # Add the change to config history
    session.config_history.append({
        'field': field_name_str,
        'old_value': old_value_formatted,
        'new_value': new_value_formatted,
        'timestamp': block_timestamp
    })
    
    # Update the timestamp
    session.updated_at = block_timestamp
    
    # Save the updated session model
    await session.save()
    
    ctx.logger.info(
        f"Game session config updated: {session_address}, field={field_name_str}, "
        f"old_value={old_value_formatted}, new_value={new_value_formatted}"
    )