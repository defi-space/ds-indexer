from defi_space_indexer import models as models
from defi_space_indexer.types.game_session.starknet_events.agent_updated import AgentUpdatedPayload
from dipdup.context import HandlerContext
from dipdup.models.starknet import StarknetEvent


async def on_agent_updated(
    ctx: HandlerContext,
    event: StarknetEvent[AgentUpdatedPayload],
) -> None:
    # Extract data from event payload
    agent_index = event.payload.agent_index
    agent_address = f'0x{event.payload.agent_address:x}'
    old_total_staked = event.payload.old_total_staked
    new_total_staked = event.payload.new_total_staked
    session_address = f'0x{event.payload.session_address:x}'
    block_timestamp = event.payload.block_timestamp
    
    # Check if agent exists
    agent = await models.Agent.get_or_none(
        address=agent_address,
        session_address=session_address
    )
    
    if not agent:
        ctx.logger.warning(
            f"Agent {agent_address} with index {agent_index} in session {session_address} "
            f"not found when updating"
        )
        return
    
    # Update the agent's total_staked value
    agent.total_staked = new_total_staked
    agent.updated_at = block_timestamp
    await agent.save()
    
    # Also update the session's updated_at timestamp
    session = await models.GameSession.get_or_none(address=session_address)
    if session:
        session.updated_at = block_timestamp
        await session.save()
    
    ctx.logger.info(
        f"Agent updated: index={agent_index}, address={agent_address}, "
        f"old_total_staked={old_total_staked}, new_total_staked={new_total_staked}, "
        f"session={session_address}"
    )