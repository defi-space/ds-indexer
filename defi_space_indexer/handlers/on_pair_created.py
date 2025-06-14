from dipdup.context import HandlerContext
from dipdup.models.starknet import StarknetEvent

from defi_space_indexer import models as models
from defi_space_indexer.types.amm_factory.starknet_events.pair_created import PairCreatedPayload
from defi_space_indexer.utils import get_token_info


async def on_pair_created(
    ctx: HandlerContext,
    event: StarknetEvent[PairCreatedPayload],
) -> None:
    # Extract data from event payload
    token0_address = f'0x{event.payload.token0:x}'
    token1_address = f'0x{event.payload.token1:x}'
    pair_address = f'0x{event.payload.pair:x}'
    total_pairs = event.payload.total_pairs
    factory_address = f'0x{event.payload.factory_address:x}'
    game_session_id = event.payload.game_session_id
    block_timestamp = event.payload.block_timestamp

    # Get factory from database
    factory = await models.AmmFactory.get_or_none(address=factory_address)
    if not factory:
        ctx.logger.warning(f'AmmFactory {factory_address} not found when creating pair')
        return

    # Update factory total pair count
    factory.num_of_pairs = total_pairs
    factory.updated_at = block_timestamp
    await factory.save()

    # Fetch token names and symbols
    token0_name, token0_symbol, token0_decimals = await get_token_info(token0_address)
    token1_name, token1_symbol, token1_decimals = await get_token_info(token1_address)

    # LP token typically follows a format like "TOKEN0-TOKEN1 LP"
    lp_token_name, lp_token_symbol, _ = await get_token_info(pair_address)

    # Check if pair already exists
    pair = await models.Pair.get_or_none(address=pair_address)
    if pair:
        ctx.logger.info(f'Pair {pair_address} already exists, updating')
        pair.factory_address = factory_address
        pair.token0_address = token0_address
        pair.token1_address = token1_address
        pair.token0_symbol = token0_symbol
        pair.token1_symbol = token1_symbol
        pair.token0_name = token0_name
        pair.token1_name = token1_name
        pair.lp_token_symbol = lp_token_symbol
        pair.lp_token_name = lp_token_name
        pair.game_session_id = game_session_id
        pair.updated_at = block_timestamp
        pair.factory = factory
        await pair.save()
        return

    # Create contract and index for the new pair
    contract_name = f'pair_{pair_address[-8:]}'

    await ctx.add_contract(name=contract_name, kind='starknet', address=pair_address, typename='amm_pair')

    index_name = f'{contract_name}_events'
    await ctx.add_index(name=index_name, template='pair_events', values={'contract': contract_name})

    # Create a new pair record
    pair = await models.Pair.create(
        address=pair_address,
        factory_address=factory_address,
        token0_address=token0_address,
        token1_address=token1_address,
        token0_symbol=token0_symbol,
        token1_symbol=token1_symbol,
        token0_name=token0_name,
        token1_name=token1_name,
        lp_token_symbol=lp_token_symbol,
        lp_token_name=lp_token_name,
        reserve0=0,
        reserve1=0,
        total_supply=0,
        klast=0,
        price_0_cumulative_last=0,
        price_1_cumulative_last=0,
        block_timestamp_last=block_timestamp,
        game_session_id=game_session_id,
        created_at=block_timestamp,
        updated_at=block_timestamp,
        factory=factory,
    )

    ctx.logger.info(
        f'Pair created: address={pair_address}, factory={factory_address}, '
        f'token0={token0_address} ({token0_symbol}), token1={token1_address} ({token1_symbol}), '
        f'game_session_id={game_session_id}, added for indexing as {contract_name}'
    )
