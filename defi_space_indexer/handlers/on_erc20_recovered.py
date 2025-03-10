from dipdup.context import HandlerContext
from dipdup.models.starknet import StarknetEvent
from defi_space_indexer.types.farming_reactor.starknet_events.erc20_recovered import ERC20RecoveredPayload

async def on_erc20_recovered(
    ctx: HandlerContext,
    event: StarknetEvent[ERC20RecoveredPayload],
) -> None:
    """Handle ERC20Recovered event from Reactor contract."""
    # Just log the event, no state changes needed
    print(f"ERC20Recovered event: {event.data.transaction_hash}")