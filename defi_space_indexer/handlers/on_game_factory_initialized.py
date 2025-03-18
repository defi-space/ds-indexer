from dipdup.context import HandlerContext
from dipdup.models.starknet import StarknetEvent
from defi_space_indexer.models.game_models import GameFactory
from defi_space_indexer.types.game_factory.starknet_events.factory_initialized import FactoryInitializedPayload

async def on_game_factory_initialized(
    ctx: HandlerContext,
    event: StarknetEvent[FactoryInitializedPayload],
) -> None:
    """Handle FactoryInitialized event from GameFactory contract.
    
    Creates a new factory record for the game protocol. Important for:
    - Initializing the game factory tracking
    - Setting up game protocol configuration
    - Establishing ownership
    """
    factory_address = hex(event.payload.factory_address)
    
    # Create new game factory record
    factory = GameFactory(
        address=factory_address,
        num_of_sessions=0,
        owner=hex(event.payload.owner),
        game_session_class_hash=hex(event.payload.game_session_class_hash),
        config_history=[],
        created_at=event.payload.block_timestamp,
        updated_at=event.payload.block_timestamp,
    )
    await factory.save() 