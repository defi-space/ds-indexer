from dipdup.context import HandlerContext
from dipdup.models.starknet import StarknetEvent
from defi_space_indexer.models.amm_models import Pair, Factory
from defi_space_indexer.types.amm_factory.starknet_events.pair_created import PairCreatedPayload

async def on_pair_created(
    ctx: HandlerContext,
    event: StarknetEvent[PairCreatedPayload],
) -> None:
    """Handle PairCreated event from Factory contract."""
    factory = await Factory.get_or_none(address=event.data.from_address)
    if factory is None:
        ctx.logger.info(f"Factory not found: {event.data.from_address}")
        return
    
    # Create contract and index for the new pair
    pair_address = hex(event.payload.pair)
    contract_name = f'pair_{pair_address[-8:]}'
    
    await ctx.add_contract(
        name=contract_name,
        kind='starknet',
        address=pair_address,
        typename='amm_pair'
    )
    
    index_name = f'{contract_name}_events'
    await ctx.add_index(
        name=index_name,
        template='pair_events',
        values={'contract': contract_name}
    )
    
    # Create new pair record
    pair = Pair(
        address=pair_address,
        factory_address=event.data.from_address,
        token0_address=hex(event.payload.token0),
        token1_address=hex(event.payload.token1),
        reserve0=0,
        reserve1=0,
        total_supply=0,
        klast=0,
        created_at=event.payload.block_timestamp,
        updated_at=event.payload.block_timestamp,
        price_0_cumulative_last=0,
        price_1_cumulative_last=0,
        block_timestamp_last=event.payload.block_timestamp,
        token0_price=0,
        token1_price=0,
        volume_24h=0,
        tvl_usd=0,
        apy_24h=0,
        accumulated_fees_token0=0,
        accumulated_fees_token1=0,
        factory=factory,
    )
    await pair.save()
    
    # Update factory
    factory.num_of_pairs = event.payload.total_pairs
    factory.updated_at = event.payload.block_timestamp
    await factory.save()