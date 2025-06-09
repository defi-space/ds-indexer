from dipdup.context import HandlerContext
from dipdup.models.starknet import StarknetEvent

from defi_space_indexer import models as models
from defi_space_indexer.types.game_factory.starknet_events.game_session_class_hash_updated import (
    GameSessionClassHashUpdatedPayload,
)


async def on_game_session_class_hash_updated(
    ctx: HandlerContext,
    event: StarknetEvent[GameSessionClassHashUpdatedPayload],
) -> None:
    # Extract data from event payload
    old_hash = f'0x{event.payload.old_hash:x}'
    new_hash = f'0x{event.payload.new_hash:x}'
    factory_address = f'0x{event.payload.factory_address:x}'
    block_timestamp = event.payload.block_timestamp

    # Get game factory from database
    factory = await models.GameFactory.get_or_none(address=factory_address)
    if not factory:
        ctx.logger.warning(f'Game factory {factory_address} not found when updating game session class hash')
        return

    # Update the game factory
    factory.game_session_class_hash = new_hash
    factory.updated_at = block_timestamp

    # Update or initialize the config_history field
    if not factory.config_history:
        factory.config_history = []

    # Add the change to config history
    factory.config_history.append(
        {'field': 'game_session_class_hash', 'old_value': old_hash, 'new_value': new_hash, 'timestamp': block_timestamp}
    )

    # Save the changes
    await factory.save()

    ctx.logger.info(
        f'Game session class hash updated: factory={factory_address}, old_hash={old_hash}, new_hash={new_hash}'
    )
