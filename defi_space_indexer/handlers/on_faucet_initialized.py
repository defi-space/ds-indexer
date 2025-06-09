from dipdup.context import HandlerContext
from dipdup.models.starknet import StarknetEvent

from defi_space_indexer import models as models
from defi_space_indexer.types.faucet.starknet_events.faucet_initialized import FaucetInitializedPayload


async def on_faucet_initialized(
    ctx: HandlerContext,
    event: StarknetEvent[FaucetInitializedPayload],
) -> None:
    # Extract data from event payload
    faucet_address = f'0x{event.payload.faucet_address:x}'
    owner = f'0x{event.payload.owner:x}'
    claim_interval = event.payload.claim_interval
    game_session_id = event.payload.game_session_id
    block_timestamp = event.payload.block_timestamp

    # Check if faucet already exists
    faucet = await models.Faucet.get_or_none(address=faucet_address)
    if faucet:
        ctx.logger.info(f'Faucet {faucet_address} already initialized, updating')
        faucet.owner = owner
        faucet.claim_interval = claim_interval
        faucet.game_session_id = game_session_id
        faucet.updated_at = block_timestamp
        await faucet.save()
        return

    # Create a new faucet record
    faucet = await models.Faucet.create(
        address=faucet_address,
        owner=owner,
        claim_interval=claim_interval,
        game_session_id=game_session_id,
        tokens_list=[],
        created_at=block_timestamp,
        updated_at=block_timestamp,
    )

    ctx.logger.info(
        f'Faucet initialized: address={faucet_address}, owner={owner}, '
        f'claim_interval={claim_interval}, game_session_id={game_session_id}'
    )
