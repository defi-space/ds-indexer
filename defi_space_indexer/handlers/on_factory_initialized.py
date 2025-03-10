from defi_space_indexer.models.amm_models import Factory
from defi_space_indexer.types.amm_factory.starknet_events.factory_initialized import FactoryInitializedPayload
from dipdup.context import HandlerContext
from dipdup.models.starknet import StarknetEvent

async def on_factory_initialized(
    ctx: HandlerContext,
    event: StarknetEvent[FactoryInitializedPayload],
) -> None:
    """Handle FactoryInitialized event from Factory contract."""
    factory = Factory (
        address=hex(event.payload.factory_address),
        num_of_pairs=0,
        total_value_locked_usd=0,
        owner=hex(event.payload.owner),
        fee_to=hex(event.payload.fee_to),
        pair_contract_class_hash=hex(event.payload.pair_contract_class_hash),
        config_history=[],
        created_at=event.payload.block_timestamp,
        updated_at=event.payload.block_timestamp,
    )
    await factory.save()
    