from dipdup.context import HandlerContext
from dipdup.models.starknet import StarknetEvent

from defi_space_indexer import models as models
from defi_space_indexer.types.amm_pair.starknet_events.price_accumulator_updated import PriceAccumulatorUpdatedPayload


async def on_price_accumulator_updated(
    ctx: HandlerContext,
    event: StarknetEvent[PriceAccumulatorUpdatedPayload],
) -> None:
    # Extract data from event payload
    price_0_cumulative_last = event.payload.price_0_cumulative_last
    price_1_cumulative_last = event.payload.price_1_cumulative_last
    pair_address = f'0x{event.payload.pair_address:x}'
    block_timestamp = event.payload.block_timestamp

    # Get pair from database
    pair = await models.Pair.get_or_none(address=pair_address)
    if not pair:
        ctx.logger.warning(f'Pair {pair_address} not found when updating price accumulators')
        return

    # Update the pair
    pair.price_0_cumulative_last = price_0_cumulative_last
    pair.price_1_cumulative_last = price_1_cumulative_last
    pair.block_timestamp_last = block_timestamp
    pair.updated_at = block_timestamp

    # Save the changes
    await pair.save()

    ctx.logger.info(
        f'Price accumulators updated: pair={pair_address}, '
        f'price_0_cumulative_last={price_0_cumulative_last}, '
        f'price_1_cumulative_last={price_1_cumulative_last}'
    )
