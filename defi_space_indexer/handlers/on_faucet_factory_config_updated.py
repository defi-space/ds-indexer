from dipdup.context import HandlerContext
from dipdup.models.starknet import StarknetEvent

from defi_space_indexer import models as models
from defi_space_indexer.types.faucet_factory.starknet_events.config_updated import ConfigUpdatedPayload


async def on_faucet_factory_config_updated(
    ctx: HandlerContext,
    event: StarknetEvent[ConfigUpdatedPayload],
) -> None:
    # Extract data from the event
    factory_address = f'0x{event.payload.faucet_factory:x}'
    field_name = event.payload.field_name
    old_value = event.payload.old_value
    new_value = event.payload.new_value
    block_timestamp = event.payload.block_timestamp

    # Update the factory model
    factory = await models.FaucetFactory.get_or_none(address=factory_address)
    if not factory:
        ctx.logger.error(f'AmmFactory {factory_address} not found when updating config field {field_name}')
        return

    # Log the config change in the history
    factory.config_history.append(
        {
            'field': field_name,
            'old_value': old_value,
            'new_value': new_value,
            'timestamp': block_timestamp,
        }
    )

    # Update the specific field if it's a tracked field
    if field_name == 'owner':
        factory.owner = new_value
    elif field_name == 'faucet_class_hash':
        factory.faucet_class_hash = new_value

    # Update the timestamp
    factory.updated_at = block_timestamp

    # Save the changes
    await factory.save()
