from dipdup.context import HandlerContext
from dipdup.models.starknet import StarknetEvent
from defi_space_indexer.models.game_models import GameSession, StakeWindow
from defi_space_indexer.types.game_session.starknet_events.stake_window_created import StakeWindowCreatedPayload

async def on_stake_window_created(
    ctx: HandlerContext,
    event: StarknetEvent[StakeWindowCreatedPayload],
) -> None:
    """Handle StakeWindowCreated event from GameSession contract.
    
    Creates a new staking window for the game session. Important for:
    - Defining when users can stake tokens
    - Establishing game timeline
    - Tracking window-specific activity
    """
    session = await GameSession.get_or_none(address=event.data.from_address)
    if session is None:
        ctx.logger.info(f"GameSession not found: {event.data.from_address}")
        return
    
    # Create new stake window
    window = StakeWindow(
        session_address=event.data.from_address,
        window_index=event.payload.window_index,
        start_time=event.payload.start_time,
        is_active=event.payload.start_time <= event.payload.block_timestamp and event.payload.block_timestamp < event.payload.end_time,
        end_time=event.payload.end_time,
        total_staked=0,
        created_at=event.payload.block_timestamp,
        session=session,
    )
    await window.save()
    
    # Update game session current window index if this is a new window
    if event.payload.window_index > session.current_window_index:
        session.current_window_index = event.payload.window_index
        session.updated_at = event.payload.block_timestamp
        await session.save() 