from dipdup.context import HandlerContext
from dipdup.models.starknet import StarknetEvent

from defi_space_indexer import models as models
from defi_space_indexer.types.game_session.starknet_events.game_suspended import GameSuspendedPayload


async def on_game_suspended(
    ctx: HandlerContext,
    event: StarknetEvent[GameSuspendedPayload],
) -> None:
    # Extract data from event payload
    block_timestamp = event.payload.block_timestamp

    # Get session address from event data
    session_address = event.data.from_address
    transaction_hash = event.data.transaction_hash

    # Get game session from database
    session = await models.GameSession.get_or_none(address=session_address)
    if not session:
        ctx.logger.warning(f'Game session {session_address} not found when suspending game')
        return

    # Update the game session
    session.game_suspended = True
    session.updated_at = block_timestamp
    await session.save()

    # Create a game event record for the game suspended event
    await models.GameEvent.create(
        transaction_hash=transaction_hash,
        created_at=block_timestamp,
        event_type=models.GameEventType.GAME_SUSPENDED,
        user_address=session.owner,  # Use the owner address since this is a system event
        amount=0,  # No amount involved in suspension
        session=session,
    )

    ctx.logger.info(f'Game suspended: session={session_address}')
