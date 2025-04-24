from defi_space_indexer import models as models
from defi_space_indexer.types.farming_factory.starknet_events.farm_created import FarmCreatedPayload
from dipdup.context import HandlerContext
from dipdup.models.starknet import StarknetEvent


async def on_farm_created(
    ctx: HandlerContext,
    event: StarknetEvent[FarmCreatedPayload],
) -> None:
    # Extract data from event payload
    factory_address = f'0x{event.payload.farm_factory:x}'
    lp_token_address = f'0x{event.payload.lp_token:x}'
    farm_address = f'0x{event.payload.farm:x}'
    farm_index = event.payload.farm_index
    game_session_id = event.payload.game_session_id
    block_timestamp = event.payload.block_timestamp
    penalty_duration = event.payload.penalty_duration
    withdraw_penalty = event.payload.withdraw_penalty
    multiplier = event.payload.multiplier
    penalty_receiver = f'0x{event.payload.penalty_receiver:x}'
    
    # Get transaction hash from event data
    transaction_hash = event.data.transaction_hash
    
    # Get the farm factory from the database
    farm_factory = await models.FarmFactory.get_or_none(address=factory_address)
    if not farm_factory:
        ctx.logger.warning(f"Farm factory {factory_address} not found when processing farm created event")
        return
    
    # Check if the farm already exists
    farm = await models.Farm.get_or_none(address=farm_address)
    if farm:
        ctx.logger.info(f"Farm {farm_address} already exists, updating details")
        farm.factory_address = factory_address
        farm.lp_token_address = lp_token_address
        farm.farm_index = farm_index
        farm.penalty_duration = penalty_duration
        farm.withdraw_penalty = withdraw_penalty
        farm.multiplier = multiplier
        farm.penalty_receiver = penalty_receiver
        farm.updated_at = block_timestamp
        await farm.save()
        return
    
    # Create contract and index for the new farm
    contract_name = f'farm_{farm_address[-8:]}'
    
    await ctx.add_contract(
        name=contract_name,
        kind='starknet',
        address=farm_address,
        typename='farming_farm'
    )
    
    index_name = f'{contract_name}_events'
    await ctx.add_index(
        name=index_name,
        template='farm_events',
        values={'contract': contract_name}
    )
    
    # Create a new farm record
    farm = await models.Farm.create(
        address=farm_address,
        factory_address=factory_address,
        lp_token_address=lp_token_address,
        farm_index=farm_index,
        owner=farm_factory.owner,
        total_staked=0,
        multiplier=multiplier,
        penalty_duration=penalty_duration,
        withdraw_penalty=withdraw_penalty,
        penalty_receiver=penalty_receiver,
        authorized_rewarders={},
        config_history=[],
        active_rewards={},
        reward_tokens=[],
        game_session_id=game_session_id,
        created_at=block_timestamp,
        updated_at=block_timestamp,
        factory=farm_factory
    )
    
    # Update farm count on the factory
    farm_factory.farm_count += 1
    farm_factory.updated_at = block_timestamp
    await farm_factory.save()
    
    ctx.logger.info(
        f"Farm created: farm={farm_address}, factory={factory_address}, "
        f"lp_token={lp_token_address}, index={farm_index}, "
        f"added for indexing as {contract_name}"
    )