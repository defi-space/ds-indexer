from dipdup.context import HandlerContext
from dipdup.models.starknet import StarknetEvent

from defi_space_indexer import models as models
from defi_space_indexer.types.game_session.starknet_events.fee_recipient_updated import FeeRecipientUpdatedPayload


async def on_fee_recipient_updated(
    ctx: HandlerContext,
    event: StarknetEvent[FeeRecipientUpdatedPayload],
) -> None:
    # Extract data from event payload
    previous_recipient = f'0x{event.payload.previous_recipient:x}'
    new_recipient = f'0x{event.payload.new_recipient:x}'
    block_timestamp = event.payload.block_timestamp

    # Get game session address from event data
    session_address = event.data.from_address

    # Get game session from database
    session = await models.GameSession.get_or_none(address=session_address)
    if not session:
        ctx.logger.warning(f'Game session {session_address} not found when updating fee recipient')
        return

    # Update the game session fee recipient
    session.fee_recipient = new_recipient
    session.updated_at = block_timestamp

    # Update or initialize the config_history field
    if not session.config_history:
        session.config_history = []

    # Add the fee recipient change to config history
    session.config_history.append(
        {
            'field': 'fee_recipient',
            'old_value': previous_recipient,
            'new_value': new_recipient,
            'timestamp': block_timestamp,
        }
    )

    # Save the changes
    await session.save()

    ctx.logger.info(
        f'Game session fee recipient updated: session={session_address}, '
        f'previous_recipient={previous_recipient}, new_recipient={new_recipient}'
    )
