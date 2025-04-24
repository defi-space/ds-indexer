from defi_space_indexer import models as models
from defi_space_indexer.types.amm_factory.starknet_events.factory_initialized import FactoryInitializedPayload
from dipdup.context import HandlerContext
from dipdup.models.starknet import StarknetEvent


async def on_factory_initialized(
    ctx: HandlerContext,
    event: StarknetEvent[FactoryInitializedPayload],
) -> None:
    # Extract data from event payload
    factory_address = f'0x{event.payload.factory_address:x}'
    owner = f'0x{event.payload.owner:x}'
    fee_to = f'0x{event.payload.fee_to:x}'
    pair_contract_class_hash = f'0x{event.payload.pair_contract_class_hash:x}'
    block_timestamp = event.payload.block_timestamp
    
    # Check if factory already exists
    factory = await models.Factory.get_or_none(address=factory_address)
    if factory:
        ctx.logger.info(f"Factory {factory_address} already initialized, updating")
        factory.owner = owner
        factory.fee_to = fee_to
        factory.pair_contract_class_hash = pair_contract_class_hash
        factory.updated_at = block_timestamp
        await factory.save()
        return
    
    # Create a new factory record
    factory = await models.Factory.create(
        address=factory_address,
        owner=owner,
        fee_to=fee_to,
        pair_contract_class_hash=pair_contract_class_hash,
        num_of_pairs=0,
        config_history=[],
        created_at=block_timestamp,
        updated_at=block_timestamp,
    )
    
    ctx.logger.info(
        f"Factory initialized: address={factory_address}, owner={owner}, "
        f"fee_to={fee_to}"
    )