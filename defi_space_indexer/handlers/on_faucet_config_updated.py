from defi_space_indexer import models as models
from defi_space_indexer.types.faucet.starknet_events.config_updated import ConfigUpdatedPayload
from dipdup.context import HandlerContext
from dipdup.models.starknet import StarknetEvent


async def on_faucet_config_updated(
    ctx: HandlerContext,
    event: StarknetEvent[ConfigUpdatedPayload],
) -> None:
    # Extract data from event payload
    field_name = event.payload.field_name
    old_value = event.payload.old_value
    new_value = event.payload.new_value
    faucet_address = f'0x{event.payload.faucet_address:x}'
    block_timestamp = event.payload.block_timestamp
    
    # Get faucet from database
    faucet = await models.Faucet.get_or_none(address=faucet_address)
    if not faucet:
        ctx.logger.warning(f"Faucet {faucet_address} not found when updating config")
        return
    
    # Convert felt252 field_name to string for readability
    field_name_str = str(field_name)
    
    # Update the appropriate field in the Faucet model based on field_name
    if field_name_str == "owner":
        faucet.owner = f'0x{new_value:x}'
    elif field_name_str == "claim_interval":
        # Use string representation for large integers to avoid overflow
        faucet.claim_interval = str(new_value)
    elif field_name_str == "game_session_id":
        # Use string representation for large integers to avoid overflow
        faucet.game_session_id = int(new_value) if int(new_value) < 2**31 else None
    # Add other fields as needed
    
    # Update or initialize the config_history field
    if not faucet.config_history:
        faucet.config_history = []
    
    # Format values based on field type
    old_value_formatted = str(old_value)
    new_value_formatted = str(new_value)
    if field_name_str in ["owner"]:
        old_value_formatted = f'0x{old_value:x}'
        new_value_formatted = f'0x{new_value:x}'
    
    # Add the change to config history
    faucet.config_history.append({
        'field': field_name_str,
        'old_value': old_value_formatted,
        'new_value': new_value_formatted,
        'timestamp': block_timestamp
    })
    
    # Update the timestamp
    faucet.updated_at = block_timestamp
    
    # Save the updated faucet model
    await faucet.save()
    
    ctx.logger.info(
        f"Faucet config updated: {faucet_address}, field={field_name_str}, "
        f"old_value={old_value_formatted}, new_value={new_value_formatted}"
    )
