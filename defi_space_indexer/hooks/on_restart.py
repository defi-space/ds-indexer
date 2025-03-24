from dipdup.context import HookContext


async def on_restart(
    ctx: HookContext,
) -> None:
    """Run on restart."""
    # Update SQL script if needed
    await ctx.execute_sql_script('on_restart')
    
    # Update all time-based fields when indexer restarts
    await ctx.fire_hook(
        'active_staking_window',
        update_all=True,
        session_address=None
    )