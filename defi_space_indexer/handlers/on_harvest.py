from dipdup.context import HandlerContext
from dipdup.models.starknet import StarknetEvent
from defi_space_indexer.models.farming_models import AgentStake, RewardEvent, Reactor
from defi_space_indexer.types.farming_reactor.starknet_events.harvest import HarvestPayload
from decimal import Decimal

async def on_harvest(
    ctx: HandlerContext,
    event: StarknetEvent[HarvestPayload],
) -> None:
    """Handle Harvest event from Reactor contract.
    
    Records reward claims by stakers. Important for:
    - Tracking reward distributions
    - Updating user reward debt
    - APY calculations
    
    Updates:
    - User's reward per token paid
    - Resets claimed rewards
    - Creates harvest event record
    """
    stake = await AgentStake.get_or_none(
        reactor_address=event.data.from_address,
        agent_address=hex(event.payload.user_address),
    )
    if stake is None:
        ctx.logger.info(f"Stake not found: {event.data.from_address} {hex(event.payload.user_address)}")
        return
    
    reactor = await Reactor.get_or_none(address=event.data.from_address)
    if reactor is None:
        ctx.logger.info(f"Reactor not found: {event.data.from_address}")
        return
    
    reward_token_hex = hex(event.payload.reward_token)
    stake.reward_per_token_paid[reward_token_hex] = Decimal(event.payload.reward_per_token_stored)
    
    if reward_token_hex in stake.rewards:
        stake.rewards[reward_token_hex] = 0
    
    stake.updated_at = event.payload.block_timestamp
    await stake.save()
    
    
    
    reward_event = RewardEvent(
        transaction_hash=event.data.transaction_hash,
        event_type='HARVEST',
        agent_address=hex(event.payload.user_address),
        reward_token=reward_token_hex,
        reward_amount=Decimal(event.payload.reward_amount),
        created_at=event.payload.block_timestamp,
        reactor=reactor,
    )
    await reward_event.save()