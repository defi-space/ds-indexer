from dipdup.context import HandlerContext
from dipdup.models.starknet import StarknetEvent
from defi_space_indexer.models.farming_models import Reactor, AgentStake, AgentStakeEvent
from defi_space_indexer.types.farming_reactor.starknet_events.deposit import DepositPayload
from decimal import Decimal

async def on_deposit(
    ctx: HandlerContext,
    event: StarknetEvent[DepositPayload],
) -> None:
    """Handle Deposit event from Reactor contract.
    
    Tracks user deposits into staking pools. Updates:
    - Reactor's total staked amount
    - User's staking position
    - Penalty timelock if applicable
    
    Critical for:
    - TVL calculations
    - User reward calculations
    - Position tracking
    """
    reactor = await Reactor.get_or_none(address=event.data.from_address)
    if reactor is None:
        ctx.logger.info(f"Reactor not found: {event.data.from_address}")
        return
    reactor.total_staked = Decimal(event.payload.total_staked)
    reactor.updated_at = event.payload.block_timestamp
    await reactor.save()
    
    stake = await AgentStake.get_or_none(
        reactor_address=event.data.from_address,
        agent_address=hex(event.payload.user_address),
    )
    if stake is None:
        stake = AgentStake(
            reactor_address=event.data.from_address,
            agent_address=hex(event.payload.user_address),
            staked_amount=Decimal(event.payload.staked_amount),
            reward_per_token_paid={},
            rewards={},
            penalty_end_time=event.payload.penalty_end_time,
            created_at=event.payload.block_timestamp,
            updated_at=event.payload.block_timestamp,
            reactor=reactor,
        )
    else:
        stake.staked_amount += Decimal(event.payload.staked_amount)
        stake.penalty_end_time = event.payload.penalty_end_time
        stake.updated_at = event.payload.block_timestamp
    await stake.save()
    
    stake_event = AgentStakeEvent(
        transaction_hash=event.data.transaction_hash,
        event_type='DEPOSIT',
        agent_address=hex(event.payload.user_address),
        staked_amount=Decimal(event.payload.staked_amount),
        created_at=event.payload.block_timestamp,
        reactor=reactor,
        stake=stake,
    )
    await stake_event.save()