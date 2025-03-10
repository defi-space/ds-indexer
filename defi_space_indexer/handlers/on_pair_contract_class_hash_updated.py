from dipdup.context import HandlerContext
from dipdup.models.starknet import StarknetEvent
from defi_space_indexer.models.amm_models import Factory
from defi_space_indexer.types.amm_factory.starknet_events.pair_contract_class_hash_updated import PairContractClassHashUpdatedPayload
async def on_pair_contract_class_hash_updated(
    ctx: HandlerContext,
    event: StarknetEvent[PairContractClassHashUpdatedPayload],
) -> None:
    """Handle PairContractClassHashUpdated event from Factory contract."""
    factory = await Factory.get_or_none(address=event.data.from_address)
    if factory is None:
        ctx.logger.info(f"Factory not found: {event.data.from_address}")
        return
    factory.pair_contract_class_hash = hex(event.payload.new_hash)
    factory.updated_at = event.payload.block_timestamp
    
    factory.config_history.append({
        'field': 'pair_contract_class_hash',
        'old_value': hex(event.payload.old_hash),
        'new_value': hex(event.payload.new_hash),
        'timestamp': event.payload.block_timestamp,
    })
    await factory.save()