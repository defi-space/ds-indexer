from decimal import Decimal
from dipdup.context import HookContext
from defi_space_indexer.models.game_models import GameFactory, GameSession
from defi_space_indexer.hooks.dexscreener import get_token_pairs

async def calculate_game_metrics(
    ctx: HookContext,
    factory_address: str | None = None,
    session_address: str | None = None,
) -> None:
    """Calculate Game metrics like TVL, token prices, and participation.
    
    Can be run for:
    - Single session (session_address provided)
    - All sessions in a factory (factory_address provided)
    - All sessions in all factories (no addresses provided)
    """
    # Get sessions to process
    if session_address:
        sessions = [await GameSession.get_or_none(address=session_address)]
    elif factory_address:
        sessions = await GameSession.filter(factory_address=factory_address)
    else:
        sessions = await GameSession.all()

    # Calculate metrics for each session
    total_tvl = Decimal(0)
    for session in sessions:
        if session is None:
            continue
            
        # Skip calculations for completed games
        if session.is_over:
            continue
        
        # Fetch price data from DexScreener for stake token
        stake_token_pairs = await get_token_pairs("starknet", session.stake_token_address)
        
        # Get USD price
        stake_token_price = Decimal(0)
        
        for pair_info in stake_token_pairs:
            if pair_info.get("priceUsd"):
                stake_token_price = Decimal(pair_info["priceUsd"])
                break
        
        # Calculate session TVL in USD
        if stake_token_price > 0:
            session_tvl = Decimal(session.total_staked) * stake_token_price
            total_tvl += session_tvl
    
    # Update factory TVL if needed
    if factory_address:
        factory = await GameFactory.get_or_none(address=factory_address)
        if factory:
            factory.total_value_locked_usd = total_tvl
            await factory.save() 