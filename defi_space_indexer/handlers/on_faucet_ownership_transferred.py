from defi_space_indexer import models as models
from defi_space_indexer.types.faucet.starknet_events.ownership_transferred import OwnershipTransferredPayload
from dipdup.context import HandlerContext
from dipdup.models.starknet import StarknetEvent


async def on_faucet_ownership_transferred(
    ctx: HandlerContext,
    event: StarknetEvent[OwnershipTransferredPayload],
) -> None:
    # Extract data from event payload
    previous_owner = f'0x{event.payload.previous_owner:x}'
    new_owner = f'0x{event.payload.new_owner:x}'
    block_timestamp = event.payload.block_timestamp
    
    # Get faucet address from event data
    faucet_address = event.data.from_address
    
    # Get faucet from database
    faucet = await models.Faucet.get_or_none(address=faucet_address)
    if not faucet:
        ctx.logger.warning(f"Faucet {faucet_address} not found when transferring ownership")
        return
    
    # Update the faucet owner
    faucet.owner = new_owner
    faucet.updated_at = block_timestamp
    
    # Save the changes
    await faucet.save()
    
    ctx.logger.info(
        f"Faucet ownership transferred: faucet={faucet_address}, "
        f"previous_owner={previous_owner}, new_owner={new_owner}"
    )