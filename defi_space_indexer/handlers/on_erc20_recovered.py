from defi_space_indexer import models as models
from defi_space_indexer.types.farming_farm.starknet_events.erc20_recovered import ERC20RecoveredPayload
from dipdup.context import HandlerContext
from dipdup.models.starknet import StarknetEvent


async def on_erc20_recovered(
    ctx: HandlerContext,
    event: StarknetEvent[ERC20RecoveredPayload],
) -> None:
    # Extract data from event payload
    token_address = f'0x{event.payload.token_address:x}'
    token_amount = event.payload.token_amount
    recipient_address = f'0x{event.payload.to:x}'
    block_timestamp = event.payload.block_timestamp
    
    # Get farm address from event data
    farm_address = event.data.from_address
    
    # Get farm from database
    farm = await models.Farm.get_or_none(address=farm_address)
    if not farm:
        ctx.logger.warning(f"Farm {farm_address} not found when processing ERC20 recovery")
        return
    
    # Update farm timestamp
    farm.updated_at = block_timestamp
    await farm.save()
    
    # Log the recovery event
    ctx.logger.info(
        f"ERC20 recovered: token={token_address}, amount={token_amount}, "
        f"recipient={recipient_address}, farm={farm_address}"
    )