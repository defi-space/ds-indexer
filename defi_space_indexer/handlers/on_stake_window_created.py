from defi_space_indexer import models as models
from defi_space_indexer.types.game_session.starknet_events.stake_window_created import StakeWindowCreatedPayload
from dipdup.context import HandlerContext
from dipdup.models.starknet import StarknetEvent


async def on_stake_window_created(
    ctx: HandlerContext,
    event: StarknetEvent[StakeWindowCreatedPayload],
) -> None:
    # Extract data from event payload
    window_index = event.payload.window_index
    start_time = event.payload.start_time
    end_time = event.payload.end_time
    block_timestamp = event.payload.block_timestamp
    
    # Get session address from event data
    session_address = event.data.from_address
    
    # Get game session from database
    session = await models.GameSession.get_or_none(address=session_address)
    if not session:
        ctx.logger.warning(f"Game session {session_address} not found when creating stake window")
        return
    
    # Create new stake window
    stake_window = await models.StakeWindow.create(
        index=window_index,
        session_address=session_address,
        start_time=start_time,
        end_time=end_time,
        is_active=False,  # Starts inactive by default
        total_staked=0,
        created_at=block_timestamp,
        updated_at=block_timestamp,
        session=session,
    )
    
    # Update session's stake windows list
    if not session.stake_windows_list:
        session.stake_windows_list = []
    
    if window_index not in session.stake_windows_list:
        session.stake_windows_list.append(window_index)
        session.updated_at = block_timestamp
        await session.save()
    
    ctx.logger.info(
        f"Stake window created: session={session_address}, index={window_index}, "
        f"start_time={start_time}, end_time={end_time}"
    )