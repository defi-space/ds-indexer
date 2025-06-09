from dipdup.context import HandlerContext
from dipdup.models.starknet import StarknetEvent

from defi_space_indexer import models as models
from defi_space_indexer.types.faucet_factory.starknet_events.faucet_class_hash_updated import (
    FaucetClassHashUpdatedPayload,
)


async def on_faucet_class_hash_updated(
    ctx: HandlerContext,
    event: StarknetEvent[FaucetClassHashUpdatedPayload],
) -> None:
    # Extract data from the event
    factory_address = f'0x{event.payload.faucet_factory:x}'
    old_hash = f'0x{event.payload.old_hash:x}'
    new_hash = f'0x{event.payload.new_hash:x}'
    block_timestamp = event.payload.block_timestamp

    # Update the factory model
    factory = await models.FaucetFactory.get_or_none(address=factory_address)
    if not factory:
        ctx.logger.error(
            f'AmmFactory {factory_address} not found when updating faucet class hash from {old_hash} to {new_hash}'
        )
        return

    # Log the class hash change in the config history
    factory.config_history.append(
        {
            'field': 'faucet_class_hash',
            'old_value': factory.faucet_class_hash,
            'new_value': new_hash,
            'timestamp': block_timestamp,
        }
    )

    # Update the class hash
    factory.faucet_class_hash = new_hash
    factory.updated_at = block_timestamp

    # Save the changes
    await factory.save()
