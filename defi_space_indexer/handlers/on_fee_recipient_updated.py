from dipdup.context import HandlerContext
from dipdup.models.starknet import StarknetEvent
from defi_space_indexer.models.game_models import GameSession
from defi_space_indexer.types.game_session.starknet_events.fee_recipient_updated import FeeRecipientUpdatedPayload

async def on_fee_recipient_updated(
    ctx: HandlerContext,
    event: StarknetEvent[FeeRecipientUpdatedPayload],
) -> None:
    """Handle FeeRecipientUpdated event from GameSession contract.
    
    Updates the fee recipient for a game session. Important for:
    - Tracking fee recipient changes
    - Monitoring administrative actions
    - Maintaining configuration history
    """
    session = await GameSession.get_or_none(address=event.data.from_address)
    if session is None:
        ctx.logger.info(f"GameSession not found: {event.data.from_address}")
        return
    
    # Record configuration change
    previous_recipient = hex(event.payload.previous_recipient)
    new_recipient = hex(event.payload.new_recipient)
    
    session.config_history.append({
        'field': 'fee_recipient',
        'old_value': previous_recipient,
        'new_value': new_recipient,
        'timestamp': event.payload.block_timestamp
    })
    
    # Update current state
    session.fee_recipient = new_recipient
    session.updated_at = event.payload.block_timestamp
    
    await session.save() 