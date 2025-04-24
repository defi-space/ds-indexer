from defi_space_indexer import models as models
from defi_space_indexer.types.faucet.starknet_events.removed_from_whitelist import RemovedFromWhitelistPayload
from dipdup.context import HandlerContext
from dipdup.models.starknet import StarknetEvent


async def on_user_removed_from_whitelist(
    ctx: HandlerContext,
    event: StarknetEvent[RemovedFromWhitelistPayload],
) -> None:
    # Extract data from event payload
    user_address = f'0x{event.payload.address:x}'
    
    # Get faucet address and timestamp from event data
    faucet_address = event.data.from_address
    block_timestamp = event.payload.block_timestamp
    
    # Get user from database
    user = await models.WhitelistedUser.get_or_none(
        address=user_address,
        faucet_address=faucet_address
    )
    
    if user:
        # Delete the user since they are no longer whitelisted
        await user.delete()
        
        ctx.logger.info(
            f"User removed from whitelist: user={user_address}, faucet={faucet_address}"
        )
    else:
        ctx.logger.warning(
            f"User {user_address} not found in faucet {faucet_address} when removing from whitelist"
        )