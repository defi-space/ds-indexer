from defi_space_indexer import models as models
from defi_space_indexer.types.farming_factory.starknet_events.farm_factory_initialized import FarmFactoryInitializedPayload
from dipdup.context import HandlerContext
from dipdup.models.starknet import StarknetEvent


async def on_farm_factory_initialized(
    ctx: HandlerContext,
    event: StarknetEvent[FarmFactoryInitializedPayload],
) -> None:
    # Extract data from event payload
    farm_factory_address = f'0x{event.payload.farm_factory:x}'
    owner = f'0x{event.payload.owner:x}'
    farm_class_hash = f'0x{event.payload.farm_class_hash:x}'
    block_timestamp = event.payload.block_timestamp
    
    # Check if farm factory already exists
    farm_factory = await models.FarmFactory.get_or_none(address=farm_factory_address)
    if farm_factory:
        ctx.logger.info(f"Farm factory {farm_factory_address} already initialized, updating")
        farm_factory.owner = owner
        farm_factory.farm_class_hash = farm_class_hash
        farm_factory.updated_at = block_timestamp
        await farm_factory.save()
        return
    
    # Create a new farm factory record
    farm_factory = await models.FarmFactory.create(
        address=farm_factory_address,
        owner=owner,
        farm_class_hash=farm_class_hash,
        farm_count=0,
        config_history=[],
        created_at=block_timestamp,
        updated_at=block_timestamp,
    )
    
    ctx.logger.info(
        f"Farm factory initialized: address={farm_factory_address}, owner={owner}, "
        f"farm_class_hash={farm_class_hash}"
    )