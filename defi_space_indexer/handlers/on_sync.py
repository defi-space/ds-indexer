from dipdup.context import HandlerContext
from dipdup.models.starknet import StarknetEvent
from defi_space_indexer.models.amm_models import Pair
from defi_space_indexer.types.amm_pair.starknet_events.sync import SyncPayload
from decimal import Decimal

async def on_sync(
    ctx: HandlerContext,
    event: StarknetEvent[SyncPayload],
) -> None:
    """Handle Sync event from Pair contract."""
    # Get the pair from database first
    pair = await Pair.get_or_none(address=event.data.from_address)
    
    # If pair doesn't exist yet, skip processing
    if not pair:
        ctx.logger.info(f"Pair {event.data.from_address} not found, skipping sync event")
        return

    # Update pair
    pair.reserve0 = Decimal(event.payload.reserve0)
    pair.reserve1 = Decimal(event.payload.reserve1)
    pair.price_0_cumulative_last = event.payload.price_0_cumulative_last
    pair.price_1_cumulative_last = event.payload.price_1_cumulative_last
    pair.block_timestamp_last = event.payload.block_timestamp
    pair.klast = Decimal(event.payload.reserve0) * Decimal(event.payload.reserve1)
    pair.updated_at = event.payload.block_timestamp

    await pair.save()