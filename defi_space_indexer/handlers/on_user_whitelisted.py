from dipdup.context import HandlerContext
from dipdup.models.starknet import StarknetEvent

from defi_space_indexer import models as models
from defi_space_indexer.types.faucet.starknet_events.added_to_whitelist import AddedToWhitelistPayload


async def on_user_whitelisted(
    ctx: HandlerContext,
    event: StarknetEvent[AddedToWhitelistPayload],
) -> None:
    # Extract data from event payload
    user_address = f'0x{event.payload.address:x}'

    # Get faucet address from event data and timestamp from payload
    faucet_address = event.data.from_address
    block_timestamp = event.payload.block_timestamp

    # Get faucet from database
    faucet = await models.Faucet.get_or_none(address=faucet_address)
    if not faucet:
        ctx.logger.warning(f'Faucet {faucet_address} not found when whitelisting user')
        return

    # Get or create user
    user, created = await models.WhitelistedUser.get_or_create(
        address=user_address,
        faucet_address=faucet_address,
        defaults={
            'created_at': block_timestamp,
            'updated_at': block_timestamp,
            'faucet': faucet,
        },
    )

    if not created:
        # Just update timestamp
        user.updated_at = block_timestamp
        await user.save()

    ctx.logger.info(f'User whitelisted: user={user_address}, faucet={faucet_address}')
