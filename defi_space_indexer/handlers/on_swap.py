from dipdup.context import HandlerContext
from dipdup.models.starknet import StarknetEvent
from defi_space_indexer.models.amm_models import SwapEvent, Pair
from defi_space_indexer.types.amm_pair.starknet_events.swap import SwapPayload
from decimal import Decimal

async def on_swap(
    ctx: HandlerContext,
    event: StarknetEvent[SwapPayload],
) -> None:
    """Handle Swap event from Pair contract.
    
    Records token swap events in the pool. Important for:
    - Volume tracking
    - Price impact analysis
    - Trading history
    
    Event includes:
    - sender: Swap initiator
    - amounts in/out: Token quantities exchanged
    - recipient: Address receiving output tokens
    """
     # Update pair
    pair = await Pair.get_or_none(address=event.data.from_address)
    if pair is None:
        ctx.logger.info(f"Pair not found: {event.data.from_address}")
        return

    pair.reserve0 = Decimal(event.payload.reserve0)
    pair.reserve1 = Decimal(event.payload.reserve1)
    pair.block_timestamp_last = event.payload.block_timestamp
    pair.klast = Decimal(event.payload.reserve0) * Decimal(event.payload.reserve1)
    pair.updated_at = event.payload.block_timestamp

    await pair.save()

    # Create swap event record
    swap_event = SwapEvent(
        transaction_hash=event.data.transaction_hash,
        sender=hex(event.payload.sender),
        amount0_in=Decimal(event.payload.amount0_in),
        amount1_in=Decimal(event.payload.amount1_in),
        amount0_out=Decimal(event.payload.amount0_out),
        amount1_out=Decimal(event.payload.amount1_out),
        created_at=event.payload.block_timestamp,
        pair=pair,
    )
    await swap_event.save()