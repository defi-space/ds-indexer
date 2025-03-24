from dipdup.context import HandlerContext
from dipdup.models.starknet import StarknetEvent
from defi_space_indexer.models.farming_models import Reactor, AgentStake, AgentStakeEvent
from defi_space_indexer.types.farming_reactor.starknet_events.withdraw import WithdrawPayload
from decimal import Decimal

async def on_withdraw(
    ctx: HandlerContext,
    event: StarknetEvent[WithdrawPayload],
) -> None:
    """Handle Withdraw event from Reactor contract."""
    reactor = await Reactor.get_or_none(address=event.data.from_address)
    if reactor is None:
        raise ValueError(f"Reactor not found: {event.data.from_address}")
    reactor.total_staked -= Decimal(event.payload.staked_amount)
    reactor.updated_at = event.payload.block_timestamp
    await reactor.save()
    
    stake = await AgentStake.get_or_none(
        reactor_address=event.data.from_address,
        agent_address=hex(event.payload.user_address),
    )
    if stake is None:
       ctx.logger.info(f"Stake not found: {event.data.from_address} {hex(event.payload.user_address)}")
       return
    stake.staked_amount -= Decimal(event.payload.staked_amount)
    stake.penalty_end_time = event.payload.penalty_end_time
    stake.updated_at = event.payload.block_timestamp
    await stake.save()
    
    stake_event = AgentStakeEvent(
        transaction_hash=event.data.transaction_hash,
        event_type='WITHDRAW',
        agent_address=hex(event.payload.user_address),
        staked_amount=Decimal(event.payload.staked_amount),
        penalty_amount=Decimal(event.payload.penalty_amount),
        created_at=event.payload.block_timestamp,
        reactor=reactor,
        stake=stake,
    )
    await stake_event.save()
    
    await ctx.fire_hook(
        'calculate_farming_metrics',
        reactor_address=event.data.from_address,
        wait=False
    )