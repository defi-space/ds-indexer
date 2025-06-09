from dipdup.context import HandlerContext
from dipdup.models.starknet import StarknetEvent

from defi_space_indexer import models as models
from defi_space_indexer.types.faucet.starknet_events.last_claim_updated import LastClaimUpdatedPayload


async def on_last_claim_updated(
    ctx: HandlerContext,
    event: StarknetEvent[LastClaimUpdatedPayload],
) -> None:
    # Extract data from event payload
    user_address = f'0x{event.payload.user_address:x}'
    previous_timestamp = event.payload.previous_timestamp
    new_timestamp = event.payload.new_timestamp
    block_timestamp = event.payload.block_timestamp

    # Get faucet address from event data
    faucet_address = event.data.from_address

    # Get the whitelisted user from database
    user = await models.WhitelistedUser.get_or_none(address=user_address, faucet_address=faucet_address)

    if not user:
        ctx.logger.warning(
            f'WhitelistedUser {user_address} for faucet {faucet_address} not found when updating last claim timestamp'
        )
        return

    # Update the user's last claim timestamp
    user.last_claim = new_timestamp
    user.updated_at = block_timestamp
    await user.save()

    ctx.logger.info(
        f'Last claim timestamp updated: user={user_address}, faucet={faucet_address}, '
        f'previous={previous_timestamp}, new={new_timestamp}'
    )
