from dipdup.context import HandlerContext
from dipdup.models.starknet import StarknetEvent
from defi_space_indexer.models.farming_models import Reactor, RewardEvent
from defi_space_indexer.types.farming_reactor.starknet_events.reward_added import RewardAddedPayload
from decimal import Decimal

async def on_reward_added(
    ctx: HandlerContext,
    event: StarknetEvent[RewardAddedPayload],
) -> None:
    """Handle RewardAdded event from Reactor contract."""
    reactor = await Reactor.get_or_none(address=event.data.from_address)
    if reactor is None:
        ctx.logger.info(f"Reactor not found: {event.data.from_address}")
        return
    
    # Update active rewards properly
    reactor.active_rewards[hex(event.payload.reward_token)] = {
        'rate': Decimal(event.payload.reward_rate),
        'reward_amount': Decimal(event.payload.reward_amount),
        'duration': event.payload.reward_duration,
        'finish': event.payload.period_finish,
        'stored': event.payload.reward_per_token_stored,
    }
    reactor.updated_at = event.payload.block_timestamp
    await reactor.save()
    
    reward_event = RewardEvent(
        transaction_hash=event.data.transaction_hash,
        event_type='REWARD_ADDED',
        reward_token=hex(event.payload.reward_token),
        reward_amount=Decimal(event.payload.reward_amount),
        reward_rate=Decimal(event.payload.reward_rate),
        reward_duration=event.payload.reward_duration,
        period_finish=event.payload.period_finish,
        user_address=hex(event.payload.rewarder),
        created_at=event.payload.block_timestamp,
        reactor=reactor,
    )
    await reward_event.save()