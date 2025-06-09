from dipdup.context import HandlerContext
from dipdup.models.starknet import StarknetEvent

from defi_space_indexer import models as models
from defi_space_indexer.types.amm_pair.starknet_events.reserve_updated import ReserveUpdatedPayload


async def on_reserve_updated(
    ctx: HandlerContext,
    event: StarknetEvent[ReserveUpdatedPayload],
) -> None:
    # Extract data from event payload
    old_reserve0 = event.payload.old_reserve0
    old_reserve1 = event.payload.old_reserve1
    new_reserve0 = event.payload.new_reserve0
    new_reserve1 = event.payload.new_reserve1
    pair_address = f'0x{event.payload.pair_address:x}'
    block_timestamp = event.payload.block_timestamp

    # Get pair from database
    pair = await models.Pair.get_or_none(address=pair_address)
    if not pair:
        ctx.logger.warning(f'Pair {pair_address} not found when updating reserves')
        return

    # Update the pair
    pair.reserve0 = new_reserve0
    pair.reserve1 = new_reserve1
    pair.updated_at = block_timestamp

    # Save the changes
    await pair.save()

    ctx.logger.info(
        f'Reserves updated: pair={pair_address}, '
        f'old_reserve0={old_reserve0}, old_reserve1={old_reserve1}, '
        f'new_reserve0={new_reserve0}, new_reserve1={new_reserve1}'
    )
