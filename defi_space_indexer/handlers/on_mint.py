from dipdup.context import HandlerContext
from dipdup.models.starknet import StarknetEvent

from defi_space_indexer import models as models
from defi_space_indexer.types.amm_pair.starknet_events.mint import MintPayload


async def on_mint(
    ctx: HandlerContext,
    event: StarknetEvent[MintPayload],
) -> None:
    # Extract data from event payload
    sender_address = f'0x{event.payload.sender:x}'
    amount0 = event.payload.amount0
    amount1 = event.payload.amount1
    reserve0 = event.payload.reserve0
    reserve1 = event.payload.reserve1
    user_liquidity = event.payload.user_liquidity
    total_supply = event.payload.total_supply
    block_timestamp = event.payload.block_timestamp

    # Get pair address from event data
    pair_address = event.data.from_address
    transaction_hash = event.data.transaction_hash

    # Get pair from database
    pair = await models.Pair.get_or_none(address=pair_address)
    if not pair:
        ctx.logger.warning(f'Pair {pair_address} not found when processing mint event')
        return

    # Update pair reserves and total supply
    pair.reserve0 = reserve0
    pair.reserve1 = reserve1
    pair.total_supply = total_supply
    pair.updated_at = block_timestamp
    await pair.save()

    # Get or create liquidity position
    # Important: This creates or retrieves a LiquidityPosition linked to the pair
    # The relationship to the pair is critical for the LiquidityEvent model
    position, created = await models.LiquidityPosition.get_or_create(
        pair_address=pair_address,
        agent_address=sender_address,
        defaults={
            'liquidity': 0,
            'deposits_token0': 0,
            'deposits_token1': 0,
            'withdrawals_token0': 0,
            'withdrawals_token1': 0,
            'created_at': block_timestamp,
            'updated_at': block_timestamp,
            'pair': pair,
        },
    )

    # Update liquidity position
    position.liquidity += user_liquidity
    position.deposits_token0 += amount0
    position.deposits_token1 += amount1
    position.updated_at = block_timestamp
    # Ensure the relationship is maintained
    position.pair = pair
    await position.save()

    # Create liquidity event record
    await models.LiquidityEvent.create(
        transaction_hash=transaction_hash,
        created_at=block_timestamp,
        event_type=models.LiquidityEventType.MINT,
        sender=sender_address,
        amount0=amount0,
        amount1=amount1,
        liquidity=user_liquidity,
        pair=pair,
        position=position,
    )

    ctx.logger.info(
        f'Mint event processed: sender={sender_address}, pair={pair_address}, '
        f'amount0={amount0}, amount1={amount1}, liquidity={user_liquidity}'
    )
