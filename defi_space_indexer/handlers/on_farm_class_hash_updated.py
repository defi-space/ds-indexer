from dipdup.context import HandlerContext
from dipdup.models.starknet import StarknetEvent

from defi_space_indexer import models as models
from defi_space_indexer.types.farming_factory.starknet_events.farm_class_hash_updated import FarmClassHashUpdatedPayload


async def on_farm_class_hash_updated(
    ctx: HandlerContext,
    event: StarknetEvent[FarmClassHashUpdatedPayload],
) -> None:
    # Extract data from event payload
    old_hash = f'0x{event.payload.old_hash:x}'
    new_hash = f'0x{event.payload.new_hash:x}'
    farm_factory_address = f'0x{event.payload.farm_factory:x}'
    block_timestamp = event.payload.block_timestamp

    # Get farm factory from database
    farm_factory = await models.FarmFactory.get_or_none(address=farm_factory_address)
    if not farm_factory:
        ctx.logger.warning(f'Farm factory {farm_factory_address} not found when updating farm class hash')
        return

    # Update the farm factory
    farm_factory.farm_class_hash = new_hash
    farm_factory.updated_at = block_timestamp

    # Update or initialize the config_history field
    if not farm_factory.config_history:
        farm_factory.config_history = []

    # Add the change to config history
    farm_factory.config_history.append(
        {'field': 'farm_class_hash', 'old_value': old_hash, 'new_value': new_hash, 'timestamp': block_timestamp}
    )

    # Save the changes
    await farm_factory.save()

    ctx.logger.info(
        f'Farm class hash updated: factory={farm_factory_address}, old_hash={old_hash}, new_hash={new_hash}'
    )
