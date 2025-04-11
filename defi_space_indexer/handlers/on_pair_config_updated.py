from defi_space_indexer import models as models
from defi_space_indexer.types.amm_pair.starknet_events.config_updated import ConfigUpdatedPayload
from dipdup.context import HandlerContext
from dipdup.models.starknet import StarknetEvent


async def on_pair_config_updated(
    ctx: HandlerContext,
    event: StarknetEvent[ConfigUpdatedPayload],
) -> None:
    # Extract data from event payload
    field_name = event.payload.field_name
    old_value = event.payload.old_value
    new_value = event.payload.new_value
    pair_address = f'0x{event.payload.pair_address:x}'
    block_timestamp = event.payload.block_timestamp
    
    # Convert felt252 field_name to string for readability
    field_name_str = str(field_name)
    
    # Get pair from database
    pair = await models.Pair.get_or_none(address=pair_address)
    if not pair:
        ctx.logger.warning(f"Pair {pair_address} not found when updating config")
        return
    
    # Update the appropriate field based on field_name
    # For AMM pairs, potential fields include game_session_id
    if field_name_str == "game_session_id":
        pair.game_session_id = int(new_value)
    # Add other fields as needed
    
    # Update timestamp
    pair.updated_at = block_timestamp
    await pair.save()
    
    ctx.logger.info(
        f"Pair config updated: pair={pair_address}, field={field_name_str}, "
        f"old_value={old_value}, new_value={new_value}"
    )