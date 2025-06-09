from dipdup.context import HandlerContext
from dipdup.models.starknet import StarknetEvent

from defi_space_indexer import models as models
from defi_space_indexer.types.farming_factory.starknet_events.ownership_transferred import OwnershipTransferredPayload


async def on_farm_factory_ownership_transferred(
    ctx: HandlerContext,
    event: StarknetEvent[OwnershipTransferredPayload],
) -> None:
    # Extract data from event payload
    previous_owner = f'0x{event.payload.previous_owner:x}'
    new_owner = f'0x{event.payload.new_owner:x}'
    farm_factory_address = f'0x{event.payload.farm_factory:x}'
    block_timestamp = event.payload.block_timestamp

    # Get farm factory from database
    farm_factory = await models.FarmFactory.get_or_none(address=farm_factory_address)
    if not farm_factory:
        ctx.logger.warning(f'Farm factory {farm_factory_address} not found when transferring ownership')
        return

    # Update the farm factory owner
    farm_factory.owner = new_owner
    farm_factory.updated_at = block_timestamp

    # Update or initialize the config_history field
    if not farm_factory.config_history:
        farm_factory.config_history = []

    # Add the ownership change to config history
    farm_factory.config_history.append(
        {'field': 'owner', 'old_value': previous_owner, 'new_value': new_owner, 'timestamp': block_timestamp}
    )

    # Save the changes
    await farm_factory.save()

    ctx.logger.info(
        f'Farm factory ownership transferred: factory={farm_factory_address}, '
        f'previous_owner={previous_owner}, new_owner={new_owner}'
    )
