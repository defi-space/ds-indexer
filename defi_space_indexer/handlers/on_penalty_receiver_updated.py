from dipdup.context import HandlerContext
from dipdup.models.starknet import StarknetEvent

from defi_space_indexer import models as models
from defi_space_indexer.types.farming_farm.starknet_events.penalty_receiver_updated import PenaltyReceiverUpdatedPayload


async def on_penalty_receiver_updated(
    ctx: HandlerContext,
    event: StarknetEvent[PenaltyReceiverUpdatedPayload],
) -> None:
    # Extract data from event payload
    previous_receiver = f'0x{event.payload.previous_receiver:x}'
    new_receiver = f'0x{event.payload.new_receiver:x}'
    block_timestamp = event.payload.block_timestamp

    # Get farm address from event data
    farm_address = event.data.from_address

    # Get farm from database
    farm = await models.Farm.get_or_none(address=farm_address)
    if not farm:
        ctx.logger.warning(f'Farm {farm_address} not found when updating penalty receiver')
        return

    # Update the farm
    farm.penalty_receiver = new_receiver
    farm.updated_at = block_timestamp

    # Update or initialize the config_history field
    if not farm.config_history:
        farm.config_history = []

    # Add the change to config history
    farm.config_history.append(
        {
            'field': 'penalty_receiver',
            'old_value': previous_receiver,
            'new_value': new_receiver,
            'timestamp': block_timestamp,
        }
    )

    # Save the changes
    await farm.save()

    ctx.logger.info(
        f'Penalty receiver updated: farm={farm_address}, '
        f'previous_receiver={previous_receiver}, new_receiver={new_receiver}'
    )
