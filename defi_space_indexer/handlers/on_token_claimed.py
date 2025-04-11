from defi_space_indexer import models as models
from defi_space_indexer.types.faucet.starknet_events.claim import ClaimPayload
from dipdup.context import HandlerContext
from dipdup.models.starknet import StarknetEvent


async def on_token_claimed(
    ctx: HandlerContext,
    event: StarknetEvent[ClaimPayload],
) -> None:
    # Extract data from event payload
    sender_address = f'0x{event.payload.sender:x}'
    token_address = f'0x{event.payload.token:x}'
    amount = event.payload.amount
    faucet_address = f'0x{event.payload.faucet_address:x}'
    total_token_amount = event.payload.total_token_amount
    claimed_at = event.payload.claimed_at
    block_timestamp = event.payload.block_timestamp
    
    # Get transaction hash from event data
    transaction_hash = event.data.transaction_hash
    
    # Get faucet from database
    faucet = await models.Faucet.get_or_none(address=faucet_address)
    if not faucet:
        ctx.logger.warning(f"Faucet {faucet_address} not found when processing claim")
        return
    
    # Get token from database
    token = await models.FaucetToken.get_or_none(
        address=token_address,
        faucet_address=faucet_address
    )
    
    if token:
        # Update token amount
        token.amount = total_token_amount
        token.updated_at = block_timestamp
        # Ensure the relationship is maintained
        token.faucet = faucet
        await token.save()
    
    # Get or create user
    user, created = await models.WhitelistedUser.get_or_create(
        address=sender_address,
        faucet_address=faucet_address,
        defaults={
            'is_whitelisted': True,
            'last_claim': claimed_at,
            'created_at': block_timestamp,
            'updated_at': block_timestamp,
            'faucet': faucet,
        }
    )
    
    if not created:
        user.last_claim = claimed_at
        user.updated_at = block_timestamp
        await user.save()
    
    # Create claim event
    if token:
        await models.ClaimEvent.create(
            transaction_hash=transaction_hash,
            created_at=block_timestamp,
            user_address=sender_address,
            token_address=token_address,
            faucet_address=faucet_address,
            amount=amount,
            faucet=faucet,
            token=token,
            user=user,
        )
    else:
        ctx.logger.warning(
            f"Token {token_address} not found in faucet {faucet_address} when creating claim event"
        )
    
    ctx.logger.info(
        f"Token claimed: sender={sender_address}, token={token_address}, "
        f"amount={amount}, faucet={faucet_address}"
    )