from dipdup.context import HandlerContext
from dipdup.models.starknet import StarknetEvent

from defi_space_indexer import models as models
from defi_space_indexer.types.amm_factory.starknet_events.config_updated import ConfigUpdatedPayload


async def on_amm_factory_config_updated(
    ctx: HandlerContext,
    event: StarknetEvent[ConfigUpdatedPayload],
) -> None:
    # Extract data from event payload
    field_name = event.payload.field_name
    old_value = event.payload.old_value
    new_value = event.payload.new_value
    factory_address = f'0x{event.payload.factory_address:x}'
    block_timestamp = event.payload.block_timestamp

    # Get factory from database
    factory = await models.AmmFactory.get_or_none(address=factory_address)
    if not factory:
        ctx.logger.warning(f'AmmFactory {factory_address} not found when updating config')
        return

    # Convert felt252 field_name to string for readability
    field_name_str = str(field_name)

    # Update the appropriate field in the AmmFactory model based on field_name
    if field_name_str == 'owner':
        factory.owner = f'0x{new_value:x}'
    elif field_name_str == 'fee_to':
        factory.fee_to = f'0x{new_value:x}'
    elif field_name_str == 'pair_contract_class_hash':
        factory.pair_contract_class_hash = f'0x{new_value:x}'
    elif field_name_str == 'game_session_id':
        factory.game_session_id = int(new_value)
    # Add other fields as needed

    # Update the config history
    if not factory.config_history:
        factory.config_history = []

    # Add the change to the config history
    factory.config_history.append(
        {
            'field': field_name_str,
            'old_value': f'0x{old_value:x}',
            'new_value': f'0x{new_value:x}',
            'timestamp': block_timestamp,
        }
    )

    # Update the timestamp
    factory.updated_at = block_timestamp

    # Save the updated factory model
    await factory.save()

    ctx.logger.info(
        f'AmmFactory config updated: {factory_address}, field={field_name_str}, '
        f'old_value=0x{old_value:x}, new_value=0x{new_value:x}'
    )
