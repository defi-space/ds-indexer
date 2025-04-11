from defi_space_indexer import models as models
from defi_space_indexer.types.faucet.starknet_events.config_updated import ConfigUpdatedPayload
from dipdup.context import HandlerContext
from dipdup.models.starknet import StarknetEvent


async def on_config_updated(
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
    elif field_name_str == "game_session_id":
        faucet.game_session_id = int(new_value)
    # Add other fields as needed
    
    # Update the timestamp
    faucet.updated_at = block_timestamp
    
    # Save the updated faucet model
    await faucet.save()
    
    ctx.logger.info(
        f"Faucet config updated: {faucet_address}, field={field_name_str}, "
        f"old_value=0x{old_value:x}, new_value=0x{new_value:x}"
    )