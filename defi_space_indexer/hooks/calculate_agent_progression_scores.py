"""
Agent Progression Score Calculation Hook

This hook calculates progression scores for each agent based on their onchain DeFi activity.
The score reflects an agent's overall participation and success in the DeFi ecosystem.

🎯 SCORING METHODOLOGY:

Total Score = Resource Balance Score + LP Token Balance Score + Farming Score

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 1. RESOURCE BALANCE SCORE
   Direct wallet token balances (ERC20 tokens) via RPC calls:
   
   Formula: Σ(token_balance × token_weight)
   
   Token Weights:
   • He3: 100 (highest value)
   • GPH, Y: 5 (medium value)
   • GRP, Dy: 2 (lower value)
   • wD, C, Nd: 1 (base tokens)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💧 2. LP TOKEN BALANCE SCORE
   LP tokens held in wallet via RPC calls:
   
   Formula: Σ(lp_balance × pool_weight)
   
   Pool Weights:
   • He3/wD: 10 (premium pool)
   • He3/GPH: 9
   • GPH/Y: 5
   • GRP/Dy: 2
   • wD/C: 1
   • C/Nd: 1 (base pools)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🚜 3. FARMING SCORE
   Farming rewards and participation via RPC calls:
   
   Formula: Σ((pending_rewards × token_weight) × farm_multiplier)
   
   Where farm_multiplier = 1 + Σ(reward_token_weight / 10)
   
   This rewards both pending rewards AND participation in high-value farms

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔢 VALUE NORMALIZATION:
   All raw contract values are converted to human-readable format using proper decimals.
   Token info is cached to minimize RPC calls.

⏰ EXECUTION:
   • Runs every 5 minutes via cron job
   • All scoring calculations done via RPC calls
   • Stores results in AgentScore model with detailed breakdowns
"""

import time
from decimal import Decimal
from typing import Dict, Optional, List, Tuple
import os

from dipdup.context import HookContext
from starknet_py.contract import Contract
from starknet_py.net.full_node_client import FullNodeClient

from defi_space_indexer.models import Agent, AgentScore, AgentStake, Farm, GameSession, Pair, Reward
from defi_space_indexer.utils import get_token_info

# Get the node URL from environment variables
RPC_URL = os.environ.get('NODE_URL', '') + '/' + os.environ.get('NODE_API_KEY', '')

# Token info cache to avoid repeated RPC calls
TOKEN_INFO_CACHE: Dict[str, Tuple[str, str, int]] = {}

# Token weights configuration
TOKEN_WEIGHTS = {
    # High value tokens
    'He3': 100,
    
    # Medium value tokens  
    'GPH': 5,
    'Y': 5,
    
    # Lower value tokens
    'GRP': 2,
    'Dy': 2,
    
    # Base tokens
    'wD': 1,
    'C': 1,
    'Nd': 1,
}

# LP Pool weights for LP token balances
LP_POOL_WEIGHTS = {
    'He3/wD': 10,      # He3 pools get highest weight
    'He3/GPH': 9,
    'GPH/Y': 5,        # Medium value pools
    'GRP/Dy': 2,       # Lower value pools
    'wD/C': 1,         # Base pools
    'C/Nd': 1,
}


async def get_cached_token_info(token_address: str) -> Tuple[str, str, int]:
    """Get token info with caching to avoid repeated RPC calls"""
    # Ensure address is properly formatted as hex string
    if isinstance(token_address, int):
        token_address = f"0x{token_address:x}"
    elif isinstance(token_address, str) and not token_address.startswith('0x'):
        # If it's a string but doesn't start with 0x, assume it's an integer string
        try:
            token_address = f"0x{int(token_address):x}"
        except ValueError:
            # If conversion fails, assume it's already a hex string without 0x
            token_address = f"0x{token_address}"
    
    if token_address not in TOKEN_INFO_CACHE:
        name, symbol, decimals = await get_token_info(token_address)
        TOKEN_INFO_CACHE[token_address] = (name, symbol, decimals)
    return TOKEN_INFO_CACHE[token_address]


def normalize_token_amount(raw_amount: Decimal, decimals: int) -> Decimal:
    """Convert raw token amount to human readable format using decimals"""
    return raw_amount / (Decimal(10) ** decimals)


def handle_u256_value(value) -> Decimal:
    """Handle u256 format values from Starknet contracts"""
    if isinstance(value, dict) and 'low' in value and 'high' in value:
        return Decimal(str(value['low'] + (value['high'] << 128)))
    elif hasattr(value, 'low') and hasattr(value, 'high'):
        return Decimal(str(value.low + (value.high << 128)))
    else:
        return Decimal(str(value))


async def calculate_agent_progression_scores(
    ctx: HookContext,
) -> None:
    """
    Calculate progression scores for agents based on their onchain state via RPC calls.
    
    Scoring Logic:
    - Resource Balance Score: Direct wallet token balances * token weights (via RPC)
    - LP Token Balance Score: LP token balances * pool weights (via RPC)  
    - Farming Score: (Pending farm rewards * token weights) * farm multiplier (via RPC)
    - Total Score: Resource + LP + Farming scores
    
    All calculations are done via RPC calls for real-time accuracy.
    
    Note: Skips calculation for suspended or completed games to save resources.
    """
    ctx.logger.info("Starting agent progression score calculation")
    
    # Clear token info cache at start of each run to get fresh data
    TOKEN_INFO_CACHE.clear()
    
    # Get all agents
    agents = await Agent.all()
    
    current_time = int(time.time())
    
    ctx.logger.info(f"Processing {len(agents)} agents")
    
    # Group agents by session to check game status efficiently
    agents_by_session = {}
    for agent in agents:
        if agent.session_address not in agents_by_session:
            agents_by_session[agent.session_address] = []
        agents_by_session[agent.session_address].append(agent)
    
    # Check game status for each session and process only active games
    active_agents = []
    skipped_sessions = 0
    
    for session_address, session_agents in agents_by_session.items():
        try:
            session = await GameSession.get(address=session_address)
            
            # Skip calculation if game is suspended or over
            if session.game_suspended or session.game_over:
                ctx.logger.info(f"Skipping session {session_address}: suspended={session.game_suspended}, over={session.game_over}")
                skipped_sessions += 1
                continue
                
            # Add agents from active sessions to processing list
            active_agents.extend(session_agents)
            
        except Exception as e:
            ctx.logger.error(f"Error checking session status for {session_address}: {e}")
            continue
    
    ctx.logger.info(f"Processing {len(active_agents)} agents from active games, skipped {skipped_sessions} suspended/completed sessions")
    
    for agent in active_agents:
        try:
            # Calculate scores via RPC calls
            resource_score = await calculate_resource_balance_score_rpc(ctx, agent.address, agent.session_address)
            lp_score = await calculate_lp_balance_score_rpc(ctx, agent.address, agent.session_address)
            farming_score = await calculate_pending_rewards_score_rpc(ctx, agent.address, agent.session_address)
            
            total_score = resource_score + lp_score + farming_score
            
            
            # Update or create AgentScore record
            agent_score, created = await AgentScore.get_or_create(
                agent_address=agent.address,
                session_address=agent.session_address,
                defaults={
                    'agent_index': agent.agent_index,
                    'resource_balance_score': resource_score,
                    'lp_position_score': lp_score,
                    'farming_score': farming_score,
                    'total_score': total_score,
                    'last_calculated_at': current_time,
                    'created_at': current_time,
                    'updated_at': current_time,
                }
            )
            
            if not created:
                # Update existing record
                agent_score.resource_balance_score = resource_score
                agent_score.lp_position_score = lp_score
                agent_score.farming_score = farming_score
                agent_score.total_score = total_score
                agent_score.last_calculated_at = current_time
                agent_score.updated_at = current_time
                await agent_score.save()
            
            ctx.logger.info(f"Agent {agent.address}: total_score={total_score}")
            
        except Exception as e:
            ctx.logger.error(f"Error calculating score for agent {agent.address}: {e}")
            continue

    # Execute SQL script for additional optimizations
    await ctx.execute_sql_script('calculate_agent_progression_scores')
    
    ctx.logger.info("Completed agent progression score calculation")


async def get_wallet_token_balance(agent_address: str, token_address: str) -> Decimal:
    """Get token balance from agent's wallet via RPC call"""
    try:
        client = FullNodeClient(node_url=RPC_URL)
        contract = await Contract.from_address(address=token_address, provider=client)
        
        # Convert agent address string to integer for the contract call
        agent_address_int = int(agent_address, 16)
        
        balance_result = await contract.functions['balance_of'].call(agent_address_int)
        balance = balance_result[0] if isinstance(balance_result, (list, tuple)) else balance_result
        
        balance_decimal = handle_u256_value(balance)
        return balance_decimal
    except Exception as e:
        return Decimal(0)


async def get_farm_pending_rewards(agent_address: str, farm_address: str) -> Dict[str, Decimal]:
    """Get pending rewards from a farm contract via RPC call"""
    try:
        client = FullNodeClient(node_url=RPC_URL)
        contract = await Contract.from_address(address=farm_address, provider=client)
        
        # Get reward tokens
        reward_tokens_result = await contract.functions['get_reward_tokens'].call()
        reward_tokens = reward_tokens_result[0] if isinstance(reward_tokens_result, (list, tuple)) else reward_tokens_result
        
        pending_rewards = {}
        
        # Get earned amount for each reward token
        for token_address in reward_tokens:
            try:
                # Convert agent address string to integer for the contract call
                agent_address_int = int(agent_address, 16)
                
                earned_result = await contract.functions['earned'].call(agent_address_int, token_address)
                earned = earned_result[0] if isinstance(earned_result, (list, tuple)) else earned_result
                
                earned_amount = handle_u256_value(earned)
                
                if earned_amount > 0:
                    pending_rewards[str(token_address)] = earned_amount
            except Exception:
                continue
        
        return pending_rewards
    except Exception:
        return {}


async def calculate_resource_balance_score_rpc(ctx: HookContext, agent_address: str, session_address: str) -> Decimal:
    """
    Calculate resource balance score using direct RPC calls for wallet token balances.
    Only considers tokens that exist in the current game session.
    """
    total_score = Decimal(0)
    
    try:
        # Get session to determine game_session_id
        session = await GameSession.get(address=session_address)
        game_session_id = session.game_session_index
        
        # Get all unique tokens from pairs in the same game session
        unique_tokens = set()
        pairs = await Pair.filter(game_session_id=game_session_id)
        
        for pair in pairs:
            unique_tokens.add(pair.token0_address)
            unique_tokens.add(pair.token1_address)
        
        # Add reward tokens from farms in the same game session
        farms = await Farm.filter(game_session_id=game_session_id)
        for farm in farms:
            if farm.reward_tokens:
                for token_addr in farm.reward_tokens:
                    unique_tokens.add(token_addr)
        
        # Get wallet balances via RPC calls
        for token_address in unique_tokens:
            try:
                balance = await get_wallet_token_balance(agent_address, token_address)
                if balance > 0:
                    # Get token info and normalize
                    _, symbol, decimals = await get_cached_token_info(token_address)
                    normalized_balance = normalize_token_amount(balance, decimals)
                    
                    # Apply weight
                    weight = TOKEN_WEIGHTS.get(symbol, 1)
                    score = normalized_balance * Decimal(str(weight))
                    total_score += score
                    
            except Exception:
                continue
        
    except Exception as e:
        ctx.logger.error(f"Error calculating resource balance score: {e}")
    
    return total_score


async def calculate_lp_balance_score_rpc(ctx: HookContext, agent_address: str, session_address: str) -> Decimal:
    """
    Calculate LP token balance score using direct RPC calls for LP token balances.
    Only considers LP tokens from the current game session.
    """
    total_score = Decimal(0)
    
    try:
        # Get session to determine game_session_id
        session = await GameSession.get(address=session_address)
        game_session_id = session.game_session_index
        
        # Get all pairs from the same game session
        pairs = await Pair.filter(game_session_id=game_session_id)
        
        for pair in pairs:
            try:
                # Get LP token balance via RPC
                lp_balance = await get_wallet_token_balance(agent_address, pair.address)
                
                if lp_balance > 0:
                    # Normalize LP balance (LP tokens typically have 18 decimals)
                    try:
                        _, _, lp_decimals = await get_cached_token_info(pair.address)
                    except Exception:
                        lp_decimals = 18  # Default for LP tokens
                    
                    normalized_balance = normalize_token_amount(lp_balance, lp_decimals)
                    
                    # Get pool weight
                    pool_key = f"{pair.token0_symbol}/{pair.token1_symbol}"
                    if pool_key not in LP_POOL_WEIGHTS:
                        pool_key = f"{pair.token1_symbol}/{pair.token0_symbol}"
                    
                    weight = LP_POOL_WEIGHTS.get(pool_key, 1)
                    score = normalized_balance * Decimal(str(weight))
                    total_score += score
                    
            except Exception:
                continue
        
    except Exception as e:
        ctx.logger.error(f"Error calculating LP balance score: {e}")
    
    return total_score


async def calculate_pending_rewards_score_rpc(ctx: HookContext, agent_address: str, session_address: str) -> Decimal:
    """
    Calculate farming score using direct RPC calls to farm contracts.
    Only considers farms from the current game session.
    
    This includes:
    1. Pending rewards from staked positions
    2. Farm reward token multiplier based on the farm's reward tokens
    """
    total_score = Decimal(0)
    
    try:
        # Get session to determine game_session_id
        session = await GameSession.get(address=session_address)
        game_session_id = session.game_session_index
        
        # Get agent's stakes in farms from the same game session
        stakes = await AgentStake.filter(agent_address=agent_address)
        
        session_farm_addresses = []
        for stake in stakes:
            farm = await Farm.get(address=stake.farm_address)
            if farm.game_session_id == game_session_id:
                session_farm_addresses.append(stake.farm_address)
        
        for farm_address in session_farm_addresses:
            try:
                # Get the farm to access reward token information
                farm = await Farm.get(address=farm_address)
                
                # Calculate farm reward token multiplier using existing Reward models
                farm_multiplier = Decimal(1)  # Base multiplier
                
                # Get reward models for this farm to access cached token symbols
                rewards = await Reward.filter(farm_address=farm_address)
                for reward in rewards:
                    try:
                        token_weight = TOKEN_WEIGHTS.get(reward.reward_token_symbol, 1)
                        # Add token weight to multiplier (higher value tokens increase farm value)
                        farm_multiplier += Decimal(str(token_weight)) / Decimal(10)  # Scale down to keep multiplier reasonable
                    except Exception:
                        continue
                
                # Get pending rewards via RPC
                pending_rewards = await get_farm_pending_rewards(agent_address, farm_address)
                
                farm_pending_score = Decimal(0)
                for token_address, reward_amount in pending_rewards.items():
                    try:
                        # Get token info and normalize
                        _, symbol, decimals = await get_cached_token_info(token_address)
                        normalized_reward = normalize_token_amount(reward_amount, decimals)
                        
                        # Apply token weight
                        weight = TOKEN_WEIGHTS.get(symbol, 1)
                        reward_score = normalized_reward * Decimal(str(weight))
                        farm_pending_score += reward_score
                        
                    except Exception:
                        continue
                
                # Apply farm multiplier to the pending rewards score
                farm_total_score = farm_pending_score * farm_multiplier
                total_score += farm_total_score
                
            except Exception:
                continue
        
    except Exception as e:
        ctx.logger.error(f"Error calculating farming score: {e}")
    
    return total_score 