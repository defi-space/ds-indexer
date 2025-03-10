from dipdup.context import HandlerContext
from dipdup.models.starknet import StarknetEvent
from defi_space_indexer.models.farming_models import Powerplant, Reactor
from defi_space_indexer.models.amm_models import Pair
from defi_space_indexer.types.farming_factory.starknet_events.reactor_created import ReactorCreatedPayload

async def on_reactor_created(
    ctx: HandlerContext,
    event: StarknetEvent[ReactorCreatedPayload],
) -> None:
    """Handle ReactorCreated event from Powerplant contract.
    
    Creates a new staking reactor for LP tokens. Important for:
    - Setting up new yield farming opportunities
    - Tracking staking pools
    - Managing reward distributions
    
    Event includes:
    - reactor: Address of new reactor
    - lp_token: Token that can be staked
    - penalty settings: Withdrawal restrictions
    """
    powerplant = await Powerplant.get_or_none(address=event.data.from_address)
    if powerplant is None:
        ctx.logger.info(f"Powerplant not found: {event.data.from_address}")
        return
    
    # Create contract and index for the new reactor
    reactor_address = hex(event.payload.reactor)
    contract_name = f'reactor_{reactor_address[-8:]}'
    
    await ctx.add_contract(
        name=contract_name,
        kind='starknet',
        address=reactor_address,
        typename='farming_reactor'
    )
    
    index_name = f'{contract_name}_events'
    await ctx.add_index(
        name=index_name,
        template='reactor_events',
        values={'contract': contract_name}
    )
    
    # Create new reactor record
    reactor = Reactor(
        address=reactor_address,
        powerplant_address=event.data.from_address,
        lp_token_address=hex(event.payload.lp_token),
        reactor_index=event.payload.reactor_index,
        created_at=event.payload.block_timestamp,
        updated_at=event.payload.block_timestamp,
        owner=powerplant.owner,
        total_staked=0,
        multiplier=event.payload.multiplier,
        locked=False,
        penalty_duration=event.payload.penalty_duration,
        withdraw_penalty=event.payload.withdraw_penalty,
        penalty_receiver=hex(event.payload.penalty_receiver),
        authorized_rewarders=[],
        config_history=[],
        active_rewards={},
        powerplant=powerplant,
    )
    await reactor.save()
    
    # Update powerplant
    powerplant.reactor_count = powerplant.reactor_count + 1
    powerplant.updated_at = event.payload.block_timestamp
    await powerplant.save()