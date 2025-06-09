from dipdup.context import HandlerContext
from dipdup.models.starknet import StarknetEvent

from defi_space_indexer import models as models
from defi_space_indexer.types.game_session.starknet_events.ownership_transferred import OwnershipTransferredPayload


async def on_ownership_transferred(
    ctx: HandlerContext,
    event: StarknetEvent[OwnershipTransferredPayload],
) -> None:
    # Extract data from event payload
    previous_owner = f'0x{event.payload.previous_owner:x}'
    new_owner = f'0x{event.payload.new_owner:x}'
    block_timestamp = event.payload.block_timestamp

    # Get session address from event data
    session_address = event.data.from_address

    # Get game session from database
    session = await models.GameSession.get_or_none(address=session_address)
    if not session:
        ctx.logger.warning(f'Game session {session_address} not found when transferring ownership')
        return

    # Update the game session owner
    session.owner = new_owner
    session.updated_at = block_timestamp

    # Update or initialize the config_history field
    if not session.config_history:
        session.config_history = []

    # Add the ownership change to config history
    session.config_history.append(
        {'field': 'owner', 'old_value': previous_owner, 'new_value': new_owner, 'timestamp': block_timestamp}
    )

    # Save the changes
    await session.save()

    ctx.logger.info(
        f'Game session ownership transferred: session={session_address}, '
        f'previous_owner={previous_owner}, new_owner={new_owner}'
    )
