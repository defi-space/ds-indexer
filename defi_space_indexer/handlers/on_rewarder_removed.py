from dipdup.context import HandlerContext
from dipdup.models.starknet import StarknetEvent
from defi_space_indexer.models.farming_models import Reactor
from defi_space_indexer.types.farming_reactor.starknet_events.rewarder_removed import RewarderRemovedPayload

async def on_rewarder_removed(
    ctx: HandlerContext,
    event: StarknetEvent[RewarderRemovedPayload],
) -> None:
    """Handle RewarderRemoved event from Reactor contract."""
    reactor = await Reactor.get_or_none(address=event.data.from_address)
    if reactor is None:
        ctx.logger.info(f"Reactor not found: {event.data.from_address}")
        return
    if hex(event.payload.rewarder) in reactor.authorized_rewarders:
        reactor.authorized_rewarders.remove(hex(event.payload.rewarder))
    reactor.updated_at = event.payload.block_timestamp
    await reactor.save()