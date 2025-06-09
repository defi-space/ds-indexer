from dipdup.context import HandlerContext
from dipdup.models.starknet import StarknetEvent

from defi_space_indexer import models as models
from defi_space_indexer.types.amm_pair.starknet_events.skim import SkimPayload


async def on_skim(
    ctx: HandlerContext,
    event: StarknetEvent[SkimPayload],
) -> None:
    # Extract data from event payload
    sender_address = f'0x{event.payload.sender:x}'
    reserve0 = event.payload.reserve0
    reserve1 = event.payload.reserve1
    amount0 = event.payload.amount0
    amount1 = event.payload.amount1
    block_timestamp = event.payload.block_timestamp

    # Get pair address from event data
    pair_address = event.data.from_address

    # Get pair from database
    pair = await models.Pair.get_or_none(address=pair_address)
    if not pair:
        ctx.logger.warning(f'Pair {pair_address} not found when processing skim event')
        return

    # Update the pair reserves
    pair.reserve0 = reserve0
    pair.reserve1 = reserve1
    pair.updated_at = block_timestamp
    await pair.save()

    ctx.logger.info(
        f'Skim event processed: sender={sender_address}, pair={pair_address}, amount0={amount0}, amount1={amount1}'
    )
