from dipdup.context import HookContext
from datetime import datetime
import time
from defi_space_indexer.models.game_models import GameSession, StakeWindow
from tortoise.expressions import Q

async def active_staking_window(
    ctx: HookContext,
    update_all: bool = False,
    session_address: str = None,
) -> None:
    """Update active staking window for GameSession and StakeWindow entities.
    
    This hook updates:
    1. GameSession.current_window_index - updates to the latest applicable window
    2. StakeWindow.is_active - updates based on current time vs window start/end times
       - Also ensures windows are marked inactive for suspended/ended games
    
    Args:
        ctx: HookContext to log and access DB
        update_all: Whether to update all sessions (True) or specific session (False)
        session_address: Specific session address to update (if update_all=False)
    """
    current_timestamp = int(time.time())
    
    # Process active sessions (not suspended, not over)
    # Query filter depends on whether we're updating specific session or all
    if update_all or session_address is None:
        active_sessions = await GameSession.filter(is_over=False, is_suspended=False)
    else:
        active_sessions = await GameSession.filter(address=session_address, is_over=False, is_suspended=False)
    
    # Process active sessions
    for session in active_sessions:
        # Get all windows for this session
        windows = await StakeWindow.filter(session_address=session.address).order_by('window_index')
        
        if not windows:
            continue
        
        # Update individual windows' active status
        for window in windows:
            old_active_status = window.is_active
            window.is_active = window.start_time <= current_timestamp and current_timestamp < window.end_time
            
            if window.is_active != old_active_status:
                await window.save()
        
        # Find current window index
        current_window = None
        for window in windows:
            if window.start_time <= current_timestamp and current_timestamp < window.end_time:
                current_window = window
                break
                
        # If no active window found, try to determine next window or if past last window
        if current_window is None:
            # Check if current time is before first window
            if current_timestamp < windows[0].start_time:
                current_window_index = 0
            else:
                # Find highest window index where current_timestamp >= end_time
                current_window_index = max(
                    (w.window_index for w in windows if current_timestamp >= w.end_time), 
                    default=session.current_window_index or 0
                )
        else:
            current_window_index = current_window.window_index
        
        # Update session if needed
        if current_window_index != session.current_window_index:
            session.current_window_index = current_window_index
            session.updated_at = current_timestamp
            await session.save()
    
    # Process inactive sessions (suspended or over) to make sure windows are properly marked as inactive
    if update_all or session_address is None:
        # Use Q objects to create proper OR condition
        inactive_sessions = await GameSession.filter(Q(is_over=True) | Q(is_suspended=True))
    else:
        # For specific session address with OR condition
        inactive_sessions = await GameSession.filter(
            Q(address=session_address) & (Q(is_over=True) | Q(is_suspended=True))
        )
    
    # Set all windows for inactive sessions to is_active=False
    for session in inactive_sessions:
        windows = await StakeWindow.filter(session_address=session.address, is_active=True)
        if windows:
            for window in windows:
                window.is_active = False
                await window.save()
