from dipdup.context import HandlerContext
from dipdup.models.starknet import StarknetEvent

from defi_space_indexer import models as models
from defi_space_indexer.types.faucet.starknet_events.claim_interval_updated import ClaimIntervalUpdatedPayload


async def on_claim_interval_updated(
    ctx: HandlerContext,
    event: StarknetEvent[ClaimIntervalUpdatedPayload],
) -> None:
    # Extract data from event payload
    old_interval = event.payload.old_interval
    new_interval = event.payload.new_interval
    block_timestamp = event.payload.block_timestamp

    # Get the faucet address from the event data
    faucet_address = event.data.from_address

    # Get faucet from database
    faucet = await models.Faucet.get_or_none(address=faucet_address)
    if not faucet:
        ctx.logger.warning(f'Faucet {faucet_address} not found when updating claim interval')
        return

    # Update the faucet model with the new claim interval
    faucet.claim_interval = new_interval
    faucet.updated_at = block_timestamp
    await faucet.save()

    ctx.logger.info(
        f'Faucet claim interval updated: {faucet_address}, old_interval={old_interval}, new_interval={new_interval}'
    )
