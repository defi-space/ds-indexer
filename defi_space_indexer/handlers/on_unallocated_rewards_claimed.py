from dipdup.context import HandlerContext
from dipdup.models.starknet import StarknetEvent
from defi_space_indexer.models.farming_models import Reactor
from defi_space_indexer.types.farming_reactor.starknet_events.unallocated_rewards_claimed import UnallocatedRewardsClaimedPayload
from decimal import Decimal

async def on_unallocated_rewards_claimed(
    ctx: HandlerContext,
    event: StarknetEvent[UnallocatedRewardsClaimedPayload],
) -> None:
    """Handle UnallocatedRewardsClaimed event from Reactor contract."""
    reactor = await Reactor.get_or_none(address=event.data.from_address)
    if reactor is None:
        ctx.logger.info(f"Reactor not found: {event.data.from_address}")
        return
    # Update unallocated rewards in active_rewards
    if event.payload.reward_token in reactor.active_rewards:
        reactor.active_rewards[hex(event.payload.reward_token)]['unallocated'] = Decimal(event.payload.unallocated_rewards)
    reactor.updated_at = event.payload.block_timestamp
    await reactor.save() 