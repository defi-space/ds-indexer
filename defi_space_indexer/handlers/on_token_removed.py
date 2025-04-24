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
    transaction_hash = event.data.transaction_hash
    
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
        ctx.logger.info(
            f"Removing token {token_address} from faucet {faucet_address}, "
            f"claim amount: {token.claim_amount}, amount: {token.amount}, "
            f"claimed amount: {token.claimed_amount}"
        )
        
        # Create claim event to track token removal
        await models.ClaimEvent.create(
            transaction_hash=transaction_hash,
            created_at=block_timestamp,
            event_type=models.ClaimEventType.TOKEN_REMOVED,
            user_address=faucet.owner,  # Using faucet owner as the user who removed the token
            token_address=token_address,
            faucet_address=faucet_address,
            amount=token.amount,  # Recording the amount that was removed
            faucet=faucet,
            token=token,
            user=None,  # No specific user for token removal
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