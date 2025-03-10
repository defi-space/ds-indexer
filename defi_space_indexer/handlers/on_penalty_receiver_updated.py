from dipdup.context import HandlerContext
from dipdup.models.starknet import StarknetEvent
from defi_space_indexer.models.farming_models import Reactor
from defi_space_indexer.types.farming_reactor.starknet_events.penalty_receiver_updated import PenaltyReceiverUpdatedPayload

async def on_penalty_receiver_updated(
    ctx: HandlerContext,
    event: StarknetEvent[PenaltyReceiverUpdatedPayload],
) -> None:
    """Handle PenaltyReceiverUpdated event from Reactor contract."""
    reactor = await Reactor.get_or_none(address=event.data.from_address)
    if reactor is None:
        ctx.logger.info(f"Reactor not found: {event.data.from_address}")
        return
    reactor.penalty_receiver = hex(event.payload.new_receiver)
    reactor.updated_at = event.payload.block_timestamp
    reactor.config_history.append({
        'field': 'penalty_receiver',
        'old_value': hex(event.payload.previous_receiver),
        'new_value': hex(event.payload.new_receiver),
        'timestamp': event.payload.block_timestamp,
    })
    await reactor.save()