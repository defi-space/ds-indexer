from dipdup.context import HandlerContext
from dipdup.models.starknet import StarknetEvent
from defi_space_indexer.models.amm_models import Pair, LiquidityEvent, LiquidityPosition
from defi_space_indexer.types.amm_pair.starknet_events.mint import MintPayload
from decimal import Decimal

async def on_mint(
    ctx: HandlerContext,
    event: StarknetEvent[MintPayload],
) -> None:
    """Handle Mint event from Pair contract.
    
    Triggered when liquidity is added to a pair. Updates:
    - Pair total supply
    - User's liquidity position
    - Creates a record of the mint event
    
    The event contains:
    - sender: Address adding liquidity
    - amount0/amount1: Token amounts added
    - liquidity: LP tokens minted
    """
    # Update pair
    pair = await Pair.get_or_none(address=event.data.from_address)
    if pair is None:
        ctx.logger.info(f"Pair not found: {event.data.from_address}")
        return

    pair.total_supply = Decimal(event.payload.total_supply)
    pair.updated_at = event.payload.block_timestamp
    pair.reserve0 = Decimal(event.payload.reserve0)
    pair.reserve1 = Decimal(event.payload.reserve1)
    pair.block_timestamp_last = event.payload.block_timestamp
    pair.klast = Decimal(event.payload.reserve0) * Decimal(event.payload.reserve1)
    await pair.save()
    
    # Update or create position
    position = await LiquidityPosition.get_or_none(
        pair_address=event.data.from_address,
        user_address=hex(event.payload.sender),
    )
    if position is None:
        position = LiquidityPosition(
            pair_address=event.data.from_address,
            user_address=hex(event.payload.sender),
            liquidity=Decimal(event.payload.user_liquidity),
            deposits_token0=Decimal(event.payload.amount0),
            deposits_token1=Decimal(event.payload.amount1),
            withdrawals_token0=Decimal(0),
            withdrawals_token1=Decimal(0),
            created_at=event.payload.block_timestamp,
            updated_at=event.payload.block_timestamp,
            pair=pair,
        )
    else:
        position.liquidity = Decimal(event.payload.user_liquidity)
        position.deposits_token0 += Decimal(event.payload.amount0)
        position.deposits_token1 += Decimal(event.payload.amount1)
        position.updated_at = event.payload.block_timestamp

    await position.save()
    
    # Create event record
    mint_event = LiquidityEvent(
        transaction_hash=event.data.transaction_hash,
        event_type='MINT',
        sender=hex(event.payload.sender),
        amount0=Decimal(event.payload.amount0),
        amount1=Decimal(event.payload.amount1),
        liquidity=Decimal(event.payload.total_liquidity),
        created_at=event.payload.block_timestamp,
        pair=pair,
        position=position,
    )
    await mint_event.save()