from defi_space_indexer import models as models
from defi_space_indexer.types.game_session.starknet_events.game_initialized import GameInitializedPayload
from dipdup.context import HandlerContext
from dipdup.models.starknet import StarknetEvent


async def on_game_initialized(
    ctx: HandlerContext,
    event: StarknetEvent[GameInitializedPayload],
) -> None:
    # Extract data from event payload
    owner = f'0x{event.payload.owner:x}'
    user_stake_token_address = f'0x{event.payload.user_stake_token_address:x}'
    token_win_condition_address = f'0x{event.payload.token_win_condition_address:x}'
    token_win_condition_threshold = event.payload.token_win_condition_threshold
    burn_fee_percentage = event.payload.burn_fee_percentage
    platform_fee_percentage = event.payload.platform_fee_percentage
    fee_recipient = f'0x{event.payload.fee_recipient:x}'
    number_of_stake_windows = event.payload.number_of_stake_windows
    number_of_agents = event.payload.number_of_agents
    block_timestamp = event.payload.block_timestamp
    
    # Get session address from event data
    session_address = event.data.from_address
    transaction_hash = event.data.transaction_hash
    
    # Check if game session already exists
    session = await models.GameSession.get_or_none(address=session_address)
    if session:
        ctx.logger.info(f"Game session {session_address} already initialized, updating")
        session.owner = owner
        session.user_stake_token_address = user_stake_token_address
        session.token_win_condition_address = token_win_condition_address
        session.token_win_condition_threshold = token_win_condition_threshold
        session.burn_fee_percentage = burn_fee_percentage
        session.platform_fee_percentage = platform_fee_percentage
        session.fee_recipient = fee_recipient
        session.number_of_stake_windows = number_of_stake_windows
        session.number_of_agents = number_of_agents
        session.updated_at = block_timestamp
        await session.save()
        
        # Create a game event record for the re-initialization
        await models.GameEvent.create(
            transaction_hash=transaction_hash,
            created_at=block_timestamp,
            event_type=models.GameEventType.GAME_INITIALIZED,
            user_address=owner,
            amount=token_win_condition_threshold,  # Use the threshold as the relevant amount
            session=session,
        )
        
        return
    
    # Get factory address (we need to figure out which factory created this session)
    # Typically, you would expect another event or some context to provide this
    # For now, we'll use a placeholder and suggest how this could be resolved
    factory_address = None
    # Get potential factories and check their sessions list
    factories = await models.GameFactory.all()
    for factory in factories:
        if session_address in factory.game_sessions_list:
            factory_address = factory.address
            break
    
    if not factory_address:
        ctx.logger.warning(f"Could not determine factory for game session {session_address}")
        # Default to the first factory or handle this case as appropriate for your application
        if factories:
            factory_address = factories[0].address
        else:
            ctx.logger.error("No game factories found in database")
            return
    
    # Create a new game session record
    session = await models.GameSession.create(
        address=session_address,
        game_factory=factory_address,
        user_stake_token_address=user_stake_token_address,
        token_win_condition_address=token_win_condition_address,
        token_win_condition_threshold=token_win_condition_threshold,
        owner=owner,
        burn_fee_percentage=burn_fee_percentage,
        platform_fee_percentage=platform_fee_percentage,
        fee_recipient=fee_recipient,
        number_of_stake_windows=number_of_stake_windows,
        number_of_agents=number_of_agents,
        game_suspended=False,
        game_over=False,
        winning_agent_index=None,
        total_rewards=0,
        stake_windows_list=[],
        agents_list=[],
        config_history=[],
        created_at=block_timestamp,
        updated_at=block_timestamp,
    )
    
    # If we found a factory, update its reference to this session
    if factory_address:
        factory = await models.GameFactory.get(address=factory_address)
        
        # Add to sessions list and increment count
        if session_address not in factory.game_sessions_list:
            factory.game_sessions_list.append(session_address)
        
        factory.game_session_count = len(factory.game_sessions_list)
        factory.updated_at = block_timestamp
        await factory.save()
        
        # Update the session with the factory reference
        session.factory = factory
        await session.save()
    
    # Create a game event record for the initialization
    await models.GameEvent.create(
        transaction_hash=transaction_hash,
        created_at=block_timestamp,
        event_type=models.GameEventType.GAME_INITIALIZED,
        user_address=owner,
        amount=token_win_condition_threshold,  # Use the threshold as the relevant amount
        session=session,
    )
    
    ctx.logger.info(
        f"Game session initialized: address={session_address}, owner={owner}, "
        f"stake_token={user_stake_token_address}, "
        f"win_token={token_win_condition_address}, threshold={token_win_condition_threshold}"
    )