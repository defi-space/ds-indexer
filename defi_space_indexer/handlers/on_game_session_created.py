from dipdup.context import HandlerContext
from dipdup.models.starknet import StarknetEvent
from defi_space_indexer.models.game_models import GameFactory, GameSession
from defi_space_indexer.types.game_factory.starknet_events.game_session_created import GameSessionCreatedPayload

async def on_game_session_created(
    ctx: HandlerContext,
    event: StarknetEvent[GameSessionCreatedPayload],
) -> None:
    """Handle GameSessionCreated event from GameFactory contract.
    
    Creates a new game session for token staking and rewards. Important for:
    - Setting up new game opportunities
    - Tracking individual game sessions
    - Managing token win conditions and staking
    
    Event includes:
    - game_session: Address of new game session
    - stake_token: Token that can be staked
    - token_win_condition: Token for determining winner
    - fee settings: Platform and burn fees
    """
    factory = await GameFactory.get_or_none(address=hex(event.payload.factory_address))
    if factory is None:
        ctx.logger.info(f"GameFactory not found: {hex(event.payload.factory_address)}")
        return
    
    # Create contract and index for the new game session
    session_address = hex(event.payload.game_session)
    contract_name = f'game_session_{session_address[-8:]}'
    
    await ctx.add_contract(
        name=contract_name,
        kind='starknet',
        address=session_address,
        typename='game_session'
    )
    
    index_name = f'{contract_name}_events'
    await ctx.add_index(
        name=index_name,
        template='game_session_events',
        values={'contract': contract_name}
    )
    
    # Create new game session record
    session = GameSession(
        address=session_address,
        factory_address=hex(event.payload.factory_address),
        stake_token_address=hex(event.payload.stake_token),
        token_win_condition_address=hex(event.payload.token_win_condition),
        token_win_condition_threshold=event.payload.token_win_condition_threshold,
        session_index=event.payload.session_index,
        owner=hex(event.payload.creator),
        burn_fee_percentage=event.payload.burn_fee_percentage,
        platform_fee_percentage=event.payload.platform_fee_percentage,
        fee_recipient=hex(event.payload.factory_address),  # Default to factory as recipient
        number_of_stake_windows=0,  # Will be set by GameInitialized event
        number_of_agents=0,  # Will be set by GameInitialized event
        is_suspended=False,
        is_over=False,
        total_staked=0,
        config_history=[],
        created_at=event.payload.block_timestamp,
        updated_at=event.payload.block_timestamp,
        factory=factory,
    )
    await session.save()
    
    # Update factory
    factory.num_of_sessions = event.payload.total_sessions
    factory.updated_at = event.payload.block_timestamp
    await factory.save() 