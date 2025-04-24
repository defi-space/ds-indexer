from defi_space_indexer import models as models
from defi_space_indexer.types.faucet_factory.starknet_events.faucet_created import FaucetCreatedPayload
from dipdup.context import HandlerContext
from dipdup.models.starknet import StarknetEvent


async def on_faucet_created(
    ctx: HandlerContext,
    event: StarknetEvent[FaucetCreatedPayload],
) -> None:
    # Extract data from the event
    faucet_address = f'0x{event.payload.faucet:x}'
    factory_address = f'0x{event.payload.faucet_factory:x}'
    claim_interval = event.payload.claim_interval
    faucet_index = event.payload.faucet_index
    block_timestamp = event.payload.block_timestamp
    game_session_id = event.payload.game_session_id
    # Update the factory model with the new faucet count
    factory = await models.FaucetFactory.get_or_none(address=factory_address)
    if not factory:
        ctx.logger.error(f"AmmFactory {factory_address} not found when creating faucet {faucet_address}")
        return
    factory.faucet_count = event.payload.faucet_count + 1
    factory.updated_at = block_timestamp
    await factory.save()
    
    # Create contract and index for the new faucet
    contract_name = f'faucet_{faucet_address[-8:]}'
    
    await ctx.add_contract(
        name=contract_name,
        kind='starknet',
        address=faucet_address,
        typename='faucet'
    )
    
    index_name = f'{contract_name}_events'
    await ctx.add_index(
        name=index_name,
        template='faucet_events',
        values={'contract': contract_name}
    )
    
    # Create the new faucet
    faucet = models.Faucet(
        address=faucet_address,
        factory_address=factory_address,
        factory=factory,  # Set the foreign key relationship properly
        faucet_index=faucet_index,
        owner=factory.owner,  # Initially set to factory owner
        claim_interval=claim_interval,
        game_session_id=game_session_id,
        tokens_list=[],
        config_history=[],
        created_at=block_timestamp,
        updated_at=block_timestamp,
    )
    
    # Save the faucet model to the database
    await faucet.save()
    
    ctx.logger.info(
        f"Faucet created: faucet={faucet_address}, factory={factory_address}, "
        f"index={faucet_index}, added for indexing as {contract_name}"
    )