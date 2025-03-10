from dipdup.context import HandlerContext
from dipdup.models.starknet import StarknetEvent
from defi_space_indexer.models.amm_models import Factory
from defi_space_indexer.types.amm_factory.starknet_events.fees_receiver_updated import FeesReceiverUpdatedPayload

async def on_fees_receiver_updated(
    ctx: HandlerContext,
    event: StarknetEvent[FeesReceiverUpdatedPayload],
) -> None:
    """Handle FeesReceiverUpdated event from Factory contract."""
    factory = await Factory.get_or_none(address=event.data.from_address)
    if factory is None:
        ctx.logger.info(f"Factory not found: {event.data.from_address}")
        return
    factory.fee_to = hex(event.payload.new_fee_to)
    factory.updated_at = event.payload.block_timestamp
    
    factory.config_history.append({
        'field': 'fee_to',
        'old_value': hex(event.payload.previous_fee_to),
        'new_value': hex(event.payload.new_fee_to),
        'timestamp': event.payload.block_timestamp
    })
    await factory.save()