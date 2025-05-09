from defi_space_indexer import models as models
from defi_space_indexer.types.game_factory.starknet_events.game_session_created import GameSessionCreatedPayload
from dipdup.context import HandlerContext
from dipdup.models.starknet import StarknetEvent
from defi_space_indexer.utils import get_token_info

async def on_game_session_created(
    ctx: HandlerContext,
    event: StarknetEvent[GameSessionCreatedPayload],
) -> None:
    # Extract data from event payload
    game_session_address = f'0x{event.payload.game_session:x}'
    token_win_condition_address = f'0x{event.payload.token_win_condition:x}'
    stake_token_address = f'0x{event.payload.stake_token:x}'
    token_win_condition_threshold = event.payload.token_win_condition_threshold
    burn_fee_percentage = event.payload.burn_fee_percentage
    platform_fee_percentage = event.payload.platform_fee_percentage
    creator_address = f'0x{event.payload.creator:x}'
    factory_address = f'0x{event.payload.factory_address:x}'
    session_index = event.payload.session_index
    total_sessions = event.payload.total_sessions
    block_timestamp = event.payload.block_timestamp
    
    # Get game factory from database
    factory = await models.GameFactory.get_or_none(address=factory_address)
    if not factory:
        ctx.logger.warning(f"Game factory {factory_address} not found when creating game session")
        return
    
    # Update factory information
    factory.game_session_count = total_sessions
    if game_session_address not in factory.game_sessions_list:
        factory.game_sessions_list.append(game_session_address)
    factory.updated_at = block_timestamp
    await factory.save()
    
    # Check if game session already exists
    session = await models.GameSession.get_or_none(address=game_session_address)
    if session:
        ctx.logger.info(f"Game session {game_session_address} already exists, updating")
        session.game_factory = factory_address
        session.user_stake_token_address = stake_token_address
        session.token_win_condition_address = token_win_condition_address
        session.token_win_condition_threshold = token_win_condition_threshold
        session.burn_fee_percentage = burn_fee_percentage
        session.platform_fee_percentage = platform_fee_percentage
        session.owner = creator_address
        session.updated_at = block_timestamp
        session.factory = factory
        session.game_session_index = session_index
        await session.save()
        return
        
    # Create contract and index for the new game session
    contract_name = f'game_session_{game_session_address[-8:]}'
    
    await ctx.add_contract(
        name=contract_name,
        kind='starknet',
        address=game_session_address,
        typename='game_session'
    )
    
    index_name = f'{contract_name}_events'
    await ctx.add_index(
        name=index_name,
        template='game_session_events',
        values={'contract': contract_name}
    )
    
    # Get token info
    token_win_condition_name, token_win_condition_symbol, token_win_condition_decimals = await get_token_info(token_win_condition_address)
    user_stake_token_name, user_stake_token_symbol, user_stake_token_decimals = await get_token_info(stake_token_address)
    
    # Create a new game session record
    session = await models.GameSession.create(
        address=game_session_address,
        game_factory=factory_address,
        user_stake_token_address=stake_token_address,
        token_win_condition_address=token_win_condition_address,
        token_win_condition_threshold=token_win_condition_threshold,
        token_win_condition_name=token_win_condition_name,
        token_win_condition_symbol=token_win_condition_symbol,
        token_win_condition_decimals=token_win_condition_decimals,
        user_stake_token_name=user_stake_token_name,
        user_stake_token_symbol=user_stake_token_symbol,
        user_stake_token_decimals=user_stake_token_decimals,
        owner=creator_address,
        burn_fee_percentage=burn_fee_percentage,
        platform_fee_percentage=platform_fee_percentage,
        fee_recipient=creator_address,  # Default to creator unless specified elsewhere
        number_of_stake_windows=0,  # Will be updated in initialization
        number_of_agents=0,  # Will be updated in initialization
        game_suspended=False,
        game_over=False,
        winning_agent_index=None,
        total_rewards=0,
        stake_windows_list=[],
        agents_list=[],
        config_history=[],
        created_at=block_timestamp,
        updated_at=block_timestamp,
        factory=factory,
        game_session_index=session_index,
    )
    
    ctx.logger.info(
        f"Game session created: address={game_session_address}, factory={factory_address}, "
        f"creator={creator_address}, index={session_index}, total={total_sessions}, "
        f"added for indexing as {contract_name}"
    )