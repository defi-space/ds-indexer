from dipdup.context import HandlerContext
from dipdup.models.starknet import StarknetEvent

from defi_space_indexer import models as models
from defi_space_indexer.types.game_session.starknet_events.agent_created import AgentCreatedPayload


async def on_agent_created(
    ctx: HandlerContext,
    event: StarknetEvent[AgentCreatedPayload],
) -> None:
    # Extract data from event payload
    agent_index = event.payload.agent_index
    agent_address = f'0x{event.payload.agent_address:x}'
    session_address = f'0x{event.payload.session_address:x}'
    block_timestamp = event.payload.block_timestamp

    # Check if game session exists
    session = await models.GameSession.get_or_none(address=session_address)
    if not session:
        ctx.logger.warning(f'Game session {session_address} not found when creating agent')
        return

    # Create or update the Agent model
    agent, created = await models.Agent.get_or_create(
        address=agent_address,
        session_address=session_address,
        defaults={
            'agent_index': agent_index,
            'total_deposited': 0,
            'total_score': 0,
            'created_at': block_timestamp,
            'updated_at': block_timestamp,
            'session': session,  # Set the foreign key relationship
        },
    )

    if not created:
        agent.updated_at = block_timestamp
        await agent.save()

    # Update GameSession agents list if not already present
    if agent_address not in session.agents_list:
        session.agents_list.append(agent_address)
        session.updated_at = block_timestamp
        await session.save()

    ctx.logger.info(f'Agent created: index={agent_index}, address={agent_address}, session={session_address}')
