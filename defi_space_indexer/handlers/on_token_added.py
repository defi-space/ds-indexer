from defi_space_indexer import models as models
from defi_space_indexer.types.faucet.starknet_events.token_added import TokenAddedPayload
from dipdup.context import HandlerContext
from dipdup.models.starknet import StarknetEvent


async def on_token_added(
    ctx: HandlerContext,
    event: StarknetEvent[TokenAddedPayload],
) -> None:
    # Extract data from event payload
    token_address = f'0x{event.payload.token:x}'
    amount = event.payload.amount
    claim_amount = event.payload.claim_amount
    
    # Get faucet address and other data from event data
    faucet_address = event.data.from_address
    transaction_hash = event.data.transaction_hash
    block_timestamp = event.payload.block_timestamp
    
    # Get faucet from database
    faucet = await models.Faucet.get_or_none(address=faucet_address)
    if not faucet:
        ctx.logger.warning(f"Faucet {faucet_address} not found when adding token")
        return
    
    # Update faucet tokens list
    if token_address not in faucet.tokens_list:
        faucet.tokens_list.append(token_address)
        faucet.updated_at = block_timestamp
        await faucet.save()
    
    # Create or update the FaucetToken model
    token, created = await models.FaucetToken.get_or_create(
        address=token_address,
        faucet_address=faucet_address,
        defaults={
            'initial_amount': amount,
            'amount_per_claim': claim_amount,
            'total_claimed_amount': 0,  # Initialize claimed amount to zero
            'created_at': block_timestamp,
            'updated_at': block_timestamp,
            'faucet': faucet,
        }
    )
    
    if not created:
        token.initial_amount = amount
        token.amount_per_claim = claim_amount
        token.updated_at = block_timestamp
        token.faucet = faucet
        await token.save()
    
    # Create claim event to track token addition
    await models.ClaimEvent.create(
        transaction_hash=transaction_hash,
        created_at=block_timestamp,
        event_type=models.ClaimEventType.TOKEN_ADDED,
        user_address=faucet.owner,  # Using faucet owner as the user who added the token
        token_address=token_address,
        faucet_address=faucet_address,
        amount=amount,
        faucet=faucet,
        token=token,
        user=None,  # No specific user for token addition
    )
    
    ctx.logger.info(
        f"Token added to faucet: faucet={faucet_address}, token={token_address}, "
        f"amount={amount}, claim_amount={claim_amount}"
    )