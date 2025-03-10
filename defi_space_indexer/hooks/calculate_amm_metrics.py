from decimal import Decimal
from dipdup.context import HookContext
from defi_space_indexer.models.amm_models import Factory, Pair
from defi_space_indexer.hooks.dexscreener import get_token_pairs

async def calculate_amm_metrics(
    ctx: HookContext,
    factory_address: str | None = None,
    pair_address: str | None = None,
) -> None:
    """Calculate AMM metrics like TVL, APY, prices.
    
    Can be run for:
    - Single pair (pair_address provided)
    - All pairs in a factory (factory_address provided)
    - All pairs in all factories (no addresses provided)
    """
    # Get pairs to process
    if pair_address:
        pairs = [await Pair.get_or_none(address=pair_address)]
    elif factory_address:
        pairs = await Pair.filter(factory_address=factory_address)
    else:
        pairs = await Pair.all()

    # Calculate metrics for each pair
    total_tvl = Decimal(0)
    for pair in pairs:
        # Fetch price data from DexScreener
        token0_pairs = await get_token_pairs("starknet", pair.token0_address)
        token1_pairs = await get_token_pairs("starknet", pair.token1_address)
        
        # Get USD prices
        token0_price = Decimal(0)
        token1_price = Decimal(0)
        
        for pair_info in token0_pairs:
            if pair_info.get("priceUsd"):
                token0_price = Decimal(pair_info["priceUsd"])
                break
                
        for pair_info in token1_pairs:
            if pair_info.get("priceUsd"):
                token1_price = Decimal(pair_info["priceUsd"])
                break
        
        # Calculate pair metrics
        if token0_price > 0 and token1_price > 0:
            # Set token prices
            pair.token0_price = token0_price
            pair.token1_price = token1_price
            
            # Calculate TVL in USD
            tvl_token0 = Decimal(pair.reserve0) * token0_price
            tvl_token1 = Decimal(pair.reserve1) * token1_price
            pair.tvl_usd = tvl_token0 + tvl_token1
            total_tvl += pair.tvl_usd
            
            # Calculate 24h APY using fees and volume
            if pair.volume_24h > 0:
                fees_24h = Decimal(pair.volume_24h) * Decimal('0.003')  # 0.3% fee
                pair.apy_24h = (fees_24h * 365) / pair.tvl_usd if pair.tvl_usd > 0 else 0
        
        await pair.save()
    
    # Update factory TVL if needed
    if factory_address:
        factory = await Factory.get_or_none(address=factory_address)
        if factory:
            factory.total_value_locked_usd = total_tvl
            await factory.save() 