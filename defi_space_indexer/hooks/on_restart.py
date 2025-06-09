from dipdup.context import HookContext


async def on_restart(
    ctx: HookContext,
) -> None:
    """Run on restart."""
    # Update SQL script if needed
    await ctx.execute_sql_script('on_restart')
