from dipdup.context import HandlerContext
from dipdup.models.starknet import StarknetEvent
from defi_space_indexer.models.amm_models import Pair, LiquidityEvent, LiquidityPosition
from defi_space_indexer.types.amm_pair.starknet_events.burn import BurnPayload
from decimal import Decimal

async def on_burn(
    ctx: HandlerContext,
    event: StarknetEvent[BurnPayload],
) -> None:
    """Handle Burn event from Pair contract."""
    # Update pair
    pair = await Pair.get_or_none(address=event.data.from_address)
    if pair is None:
        raise ValueError(f"Pair not found: {event.data.from_address}")

    pair.total_supply = Decimal(event.payload.total_supply)
    pair.updated_at = event.payload.block_timestamp
    pair.reserve0 = Decimal(event.payload.reserve0)
    pair.reserve1 = Decimal(event.payload.reserve1)
    pair.block_timestamp_last = event.payload.block_timestamp
    pair.klast = Decimal(event.payload.reserve0) * Decimal(event.payload.reserve1)
    await pair.save()
    
    # Update or create position
    position = await LiquidityPosition.get_or_none(
        pair_address=(event.data.from_address),
        user_address=hex(event.payload.sender),
    )
    if position is None:
        ctx.logger.info(f"Liquidity position not found: {event.data.from_address} {hex(event.payload.sender)}")
        return
    position.liquidity = Decimal(event.payload.user_liquidity)
    position.withdrawals_token0 += Decimal(event.payload.amount0)
    position.withdrawals_token1 += Decimal(event.payload.amount1)
    position.updated_at = event.payload.block_timestamp
    await position.save()
    
    burn_event = LiquidityEvent(
        transaction_hash=event.data.transaction_hash,
        created_at=event.payload.block_timestamp,
        event_type='BURN',
        sender=hex(event.payload.sender),
        amount0=Decimal(event.payload.amount0),
        amount1=Decimal(event.payload.amount1),
        liquidity=Decimal(event.payload.total_liquidity),
        pair=pair,
        position=position,
    )
    await burn_event.save()