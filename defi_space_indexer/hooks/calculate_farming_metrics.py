from decimal import Decimal
from dipdup.context import HookContext
from defi_space_indexer.models.farming_models import Powerplant, Reactor, UserStake
from defi_space_indexer.models.amm_models import Pair
from defi_space_indexer.hooks.dexscreener import get_token_pairs

async def calculate_farming_metrics(
    ctx: HookContext,
    powerplant_address: str | None = None,
    reactor_address: str | None = None,
) -> None:
    """Calculate farming metrics like TVL, APR, rewards.
    
    Can be run for:
    - Single reactor (reactor_address provided)
    - All reactors in a powerplant (powerplant_address provided)
    - All reactors in all powerplants (no addresses provided)
    """
    # Get reactors to process
    if reactor_address:
        reactors = [await Reactor.get_or_none(address=reactor_address)]
    elif powerplant_address:
        reactors = await Reactor.filter(powerplant_address=powerplant_address)
    else:
        reactors = await Reactor.all()

    # Calculate metrics for each reactor
    total_tvl = Decimal(0)
    for reactor in reactors:
        # Get associated pair for LP token price
        pair = await Pair.get_or_none(address=reactor.lp_token_address)
        if pair is None:
            ctx.logger.info(f"Pair not found for reactor {reactor.address}")
            continue
        
        # Get LP token price from DexScreener
        lp_pairs = await get_token_pairs("starknet", pair.address)
        lp_price_usd = Decimal(0)
        
        for pair_info in lp_pairs:
            if pair_info.get("priceUsd"):
                lp_price_usd = Decimal(pair_info["priceUsd"])
                break
        
        # Calculate TVL using LP token price
        if lp_price_usd > 0:
            tvl_usd = Decimal(reactor.total_staked) * lp_price_usd
        else:
            # Fallback to pair TVL ratio if LP price not available
            tvl_usd = Decimal(reactor.total_staked) * Decimal(pair.tvl_usd) / Decimal(pair.total_supply) if pair.total_supply > 0 else 0
        
        total_tvl += tvl_usd
        
        # Update user stakes
        stakes = await UserStake.filter(reactor_address=reactor.address)
        for stake in stakes:
            stake_share = Decimal(stake.staked_amount) / Decimal(reactor.total_staked) if reactor.total_staked > 0 else 0
            stake.usd_value = stake_share * tvl_usd
            await stake.save()
    
    # Update powerplant TVL if needed
    if powerplant_address:
        powerplant = await Powerplant.get_or_none(address=powerplant_address)
        if powerplant:
            powerplant.total_value_locked_usd = total_tvl
            await powerplant.save() 