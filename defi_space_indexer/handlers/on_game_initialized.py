from dipdup.context import HandlerContext
from dipdup.models.starknet import StarknetEvent
from defi_space_indexer.models.game_models import GameSession
from defi_space_indexer.types.game_session.starknet_events.game_initialized import GameInitializedPayload

async def on_game_initialized(
    ctx: HandlerContext,
    event: StarknetEvent[GameInitializedPayload],
) -> None:
    """Handle GameInitialized event from GameSession contract.
    
    Initializes a game session with its configuration. Important for:
    - Setting up game parameters
    - Configuring stake windows and agents
    - Establishing fee structures
    """
    session = await GameSession.get_or_none(address=event.data.from_address)
    if session is None:
        ctx.logger.info(f"GameSession not found: {event.data.from_address}")
        return
    
    # Update session with initialization data
    session.owner = hex(event.payload.owner)
    session.fee_recipient = hex(event.payload.fee_recipient)
    session.number_of_stake_windows = event.payload.number_of_stake_windows
    session.number_of_agents = event.payload.number_of_agents
    
    # All other fields should already be set by GameSessionCreated event
    
    # Update timestamps
    session.updated_at = event.payload.block_timestamp
    
    await session.save() 