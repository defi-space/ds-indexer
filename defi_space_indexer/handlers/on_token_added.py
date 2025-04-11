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
    
    # Handle max_supply which may not exist in all versions of the contract
    max_supply = None
    if hasattr(event.payload, 'max_supply'):
        max_supply = event.payload.max_supply
        ctx.logger.info(f"Max supply information available for token {token_address}: {max_supply}")
    else:
        ctx.logger.debug(f"No max_supply field in TokenAdded event for token {token_address}")
    
    # Get faucet address and other data from event data
    faucet_address = event.data.from_address
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
            'amount': amount,
            'claim_amount': claim_amount,
            'max_supply': max_supply,
            'created_at': block_timestamp,
            'updated_at': block_timestamp,
            'faucet': faucet,
        }
    )
    
    if not created:
        token.amount = amount
        token.claim_amount = claim_amount
        if max_supply is not None:
            token.max_supply = max_supply
        token.updated_at = block_timestamp
        token.faucet = faucet
        await token.save()
    
    max_supply_str = f", max_supply={max_supply}" if max_supply is not None else ""
    ctx.logger.info(
        f"Token added to faucet: faucet={faucet_address}, token={token_address}, "
        f"amount={amount}, claim_amount={claim_amount}{max_supply_str}"
    )