from defi_space_indexer import models as models
from defi_space_indexer.types.faucet.starknet_events.token_removed import TokenRemovedPayload
from dipdup.context import HandlerContext
from dipdup.models.starknet import StarknetEvent


async def on_token_removed(
    ctx: HandlerContext,
    event: StarknetEvent[TokenRemovedPayload],
) -> None:
    # Extract data from event payload
    token_address = f'0x{event.payload.token:x}'
    block_timestamp = event.payload.block_timestamp
    
    # Get faucet address from event data
    faucet_address = event.data.from_address
    
    # Get faucet from database
    faucet = await models.Faucet.get_or_none(address=faucet_address)
    if not faucet:
        ctx.logger.warning(f"Faucet {faucet_address} not found when processing token removal")
        return
    
    # Find the token in the database
    token = await models.FaucetToken.get_or_none(
        faucet_address=faucet_address,
        address=token_address
    )
    
    if token:
        # Log before deleting
        max_supply_str = f", max_supply: {token.max_supply}" if token.max_supply is not None else ""
        ctx.logger.info(
            f"Removing token {token_address} from faucet {faucet_address}, "
            f"claim amount: {token.claim_amount}, amount: {token.amount}{max_supply_str}"
        )
        
        # Update faucet tokens list
        if token_address in faucet.tokens_list:
            faucet.tokens_list.remove(token_address)
            faucet.updated_at = block_timestamp
            await faucet.save()
        
        # Delete the token record
        await token.delete()
        
        ctx.logger.info(f"Token {token_address} removed from faucet {faucet_address}")
    else:
        ctx.logger.warning(f"Token {token_address} not found in faucet {faucet_address} when trying to remove it")