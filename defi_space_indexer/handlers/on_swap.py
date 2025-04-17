from defi_space_indexer import models as models
from defi_space_indexer.types.amm_pair.starknet_events.swap import SwapPayload
from dipdup.context import HandlerContext
from dipdup.models.starknet import StarknetEvent
import decimal


async def on_swap(
    ctx: HandlerContext,
    event: StarknetEvent[SwapPayload],
) -> None:
    # Extract data from event payload
    sender_address = f'0x{event.payload.sender:x}'
    amount0_in = event.payload.amount0_in
    amount1_in = event.payload.amount1_in
    amount0_out = event.payload.amount0_out
    amount1_out = event.payload.amount1_out
    balance0 = event.payload.balance0
    balance1 = event.payload.balance1
    reserve0 = event.payload.reserve0
    reserve1 = event.payload.reserve1
    factory_address = f'0x{event.payload.factory_address:x}'
    block_timestamp = event.payload.block_timestamp
    
    # Get pair address and transaction hash from event data
    pair_address = event.data.from_address
    transaction_hash = event.data.transaction_hash
    block_number = event.data.level
    
    # Get pair from database
    pair = await models.Pair.get_or_none(address=pair_address)
    if not pair:
        ctx.logger.warning(f"Pair {pair_address} not found when processing swap event")
        return
    
    # Calculate price impact
    # Price impact is the percentage change in the reserves ratio caused by this swap
    price_impact = None
    try:
        # Get old reserves from the pair before the update
        old_reserve0 = pair.reserve0
        old_reserve1 = pair.reserve1
        
        # Calculate price before swap (if reserves are valid)
        if old_reserve0 > 0 and old_reserve1 > 0:
            price_before = decimal.Decimal(old_reserve1) / decimal.Decimal(old_reserve0)
            price_after = decimal.Decimal(reserve1) / decimal.Decimal(reserve0)
            
            # Calculate price impact as percentage change
            if price_before > 0:
                price_impact = abs((price_after - price_before) / price_before)
    except Exception as e:
        ctx.logger.warning(f"Error calculating price impact: {e}")
    
    # Update pair reserves
    pair.reserve0 = reserve0
    pair.reserve1 = reserve1
    pair.updated_at = block_timestamp
    await pair.save()
    
    # In our payload we don't have a 'to' field, so we'll use the sender address
    # In more advanced implementations, the 'to' field would be extracted from the event payload if available
    to_address = sender_address  # Default to sender if 'to' is not in the payload
    
    # Create swap event record
    await models.SwapEvent.create(
        transaction_hash=transaction_hash,
        created_at=block_timestamp,
        block_number=block_number,
        sender=sender_address,
        to=to_address,  # Set the recipient address
        amount0_in=amount0_in,
        amount1_in=amount1_in,
        amount0_out=amount0_out,
        amount1_out=amount1_out,
        price_impact=price_impact,
        pair=pair,
    )
    
    # Calculate and log some useful metrics
    total_input_value = amount0_in + (amount1_in * reserve0 // reserve1 if reserve1 > 0 else 0)
    total_output_value = amount0_out + (amount1_out * reserve0 // reserve1 if reserve1 > 0 else 0)
    
    ctx.logger.info(
        f"Swap event processed: sender={sender_address}, pair={pair_address}, "
        f"amount0_in={amount0_in}, amount1_in={amount1_in}, "
        f"amount0_out={amount0_out}, amount1_out={amount1_out}, "
        f"price_impact={f'{price_impact:.6f}' if price_impact is not None else 'N/A'}"
    )