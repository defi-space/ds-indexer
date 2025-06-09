from dipdup.context import HandlerContext
from dipdup.models.starknet import StarknetEvent

from defi_space_indexer import models as models
from defi_space_indexer.types.game_factory.starknet_events.factory_initialized import FactoryInitializedPayload


async def on_game_factory_initialized(
    ctx: HandlerContext,
    event: StarknetEvent[FactoryInitializedPayload],
) -> None:
    # Extract data from event payload
    factory_address = f'0x{event.payload.factory_address:x}'
    owner = f'0x{event.payload.owner:x}'
    game_session_class_hash = f'0x{event.payload.game_session_class_hash:x}'
    block_timestamp = event.payload.block_timestamp

    # Check if game factory already exists
    factory = await models.GameFactory.get_or_none(address=factory_address)
    if factory:
        ctx.logger.info(f'Game factory {factory_address} already initialized, updating')
        factory.owner = owner
        factory.game_session_class_hash = game_session_class_hash
        factory.updated_at = block_timestamp
        await factory.save()
        return

    # Create a new game factory record
    factory = await models.GameFactory.create(
        address=factory_address,
        owner=owner,
        game_session_class_hash=game_session_class_hash,
        game_session_count=0,
        game_sessions_list=[],
        config_history=[],
        created_at=block_timestamp,
        updated_at=block_timestamp,
    )

    ctx.logger.info(
        f'Game factory initialized: address={factory_address}, owner={owner}, '
        f'game_session_class_hash={game_session_class_hash}'
    )
