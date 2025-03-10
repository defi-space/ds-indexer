from dipdup.context import HandlerContext
from dipdup.models.starknet import StarknetEvent
from defi_space_indexer.types.amm_pair.starknet_events.skim import SkimPayload

async def on_skim(
    ctx: HandlerContext,
    event: StarknetEvent[SkimPayload],
) -> None:
    """Handle Skim event from Pair contract."""
    # No state updates needed, just log the event
    print(f"Skim event: {event.data.transaction_hash}")