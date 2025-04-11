from defi_space_indexer import models as models
from defi_space_indexer.types.amm_pair.starknet_events.k_last_updated import KLastUpdatedPayload
from dipdup.context import HandlerContext
from dipdup.models.starknet import StarknetEvent


async def on_klast_updated(
    ctx: HandlerContext,
    event: StarknetEvent[KLastUpdatedPayload],
) -> None:
    # Extract data from event payload
    old_klast = event.payload.old_klast
    new_klast = event.payload.new_klast
    pair_address = f'0x{event.payload.pair_address:x}'
    block_timestamp = event.payload.block_timestamp
    
    # Get pair from database
    pair = await models.Pair.get_or_none(address=pair_address)
    if not pair:
        ctx.logger.warning(f"Pair {pair_address} not found when updating klast")
        return
    
    # Update the pair
    pair.klast = new_klast
    pair.updated_at = block_timestamp
    await pair.save()
    
    ctx.logger.info(
        f"Pair klast updated: pair={pair_address}, "
        f"old_klast={old_klast}, new_klast={new_klast}"
    )