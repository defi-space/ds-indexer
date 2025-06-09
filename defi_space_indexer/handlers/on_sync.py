from dipdup.context import HandlerContext
from dipdup.models.starknet import StarknetEvent

from defi_space_indexer import models as models
from defi_space_indexer.types.amm_pair.starknet_events.sync import SyncPayload


async def on_sync(
    ctx: HandlerContext,
    event: StarknetEvent[SyncPayload],
) -> None:
    # Extract data from event payload
    reserve0 = event.payload.reserve0
    reserve1 = event.payload.reserve1
    price_0_cumulative_last = event.payload.price_0_cumulative_last
    price_1_cumulative_last = event.payload.price_1_cumulative_last
    block_timestamp = event.payload.block_timestamp

    # Get pair address from event data
    pair_address = event.data.from_address

    # Get pair from database
    pair = await models.Pair.get_or_none(address=pair_address)
    if not pair:
        ctx.logger.warning(f'Pair {pair_address} not found when processing sync event')
        return

    # Update pair data
    pair.reserve0 = reserve0
    pair.reserve1 = reserve1
    pair.price_0_cumulative_last = price_0_cumulative_last
    pair.price_1_cumulative_last = price_1_cumulative_last
    pair.block_timestamp_last = block_timestamp
    pair.updated_at = block_timestamp
    await pair.save()

    ctx.logger.info(f'Sync event processed: pair={pair_address}, reserve0={reserve0}, reserve1={reserve1}')
