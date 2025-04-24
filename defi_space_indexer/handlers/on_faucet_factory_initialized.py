from defi_space_indexer import models as models
from defi_space_indexer.types.faucet_factory.starknet_events.faucet_factory_initialized import FaucetFactoryInitializedPayload
from dipdup.context import HandlerContext
from dipdup.models.starknet import StarknetEvent


async def on_faucet_factory_initialized(
    ctx: HandlerContext,
    event: StarknetEvent[FaucetFactoryInitializedPayload],
) -> None:
    # Extract data from the event
    faucet_factory_address = f'0x{event.payload.faucet_factory:x}'
    owner = f'0x{event.payload.owner:x}'
    faucet_class_hash = f'0x{event.payload.faucet_class_hash:x}'
    block_timestamp = event.payload.block_timestamp

    # Create a new FaucetFactory model
    faucet_factory = models.FaucetFactory(
        address=faucet_factory_address,
        owner=owner,
        faucet_class_hash=faucet_class_hash,
        faucet_count=0,
        game_session_id=0,  # Default to 0 until set
        config_history=[],
        created_at=block_timestamp,
        updated_at=block_timestamp,
    )

    # Save the factory model to the database
    await faucet_factory.save()