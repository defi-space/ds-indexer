"""
Agent Progression Score Calculation Hook

This hook calculates progression scores for each agent based on their onchain DeFi activity.
The score reflects an agent's overall participation and success in the DeFi ecosystem.

🎯 SCORING METHODOLOGY:

Total Score = Resource Balance Score + LP Position Score + Farming Score

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 1. RESOURCE BALANCE SCORE
   Evaluates token holdings across all positions:
   
   Components:
   • Direct wallet balances (ERC20 tokens)
   • Underlying tokens from LP positions (token0 + token1 extracted from LP shares)
   • Single-sided farm deposits
   
   Formula: Σ(token_amount_normalized × token_weight)
   
   Token Weights:
   • He3: 100 (highest value)
   • GPH, Y: 50 (medium value)
   • GRP, Dy: 25 (lower value)
   • wD, C, Nd: 5 (base tokens)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔗 2. LP POSITION SCORE
   Measures liquidity provision across different pools:
   
   Components:
   • LP tokens held in wallet
   • LP tokens staked in farms
   
   Formula: Σ(lp_amount_normalized × pool_weight)
   
   Pool Weights:
   • He3/wD: 50 (premium pool)
   • He3/GPH: 45
   • GPH/Y: 40
   • GRP/Dy: 30
   • wD/C: 20
   • C/Nd: 20 (base pools)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🚜 3. FARMING SCORE
   Rewards active yield farming participation:
   
   Components:
   • Pending/claimable rewards from farms
   
   Formula: Σ(pending_rewards_normalized × token_weight)
   
   Note: Staked LP tokens are counted in LP Position Score, not here
   Reward Weights: Use same token weights as resource balances

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔢 VALUE NORMALIZATION:
   All raw contract values are converted to human-readable format using proper decimals:
   • Queries token.decimals() for each token
   • Normalizes: raw_amount / (10^decimals)
   • Caches token info to minimize RPC calls

⏰ EXECUTION:
   • Runs every 5 minutes via cron job
   • Processes ALL agents, but scores are calculated PER GAME SESSION
   • Only considers activities within each agent's specific game session
   • Stores results in AgentScore model with detailed breakdowns
   • Non-atomic to avoid blocking main indexer

📈 SCORE INTERPRETATION:
   Higher scores indicate:
   • Larger token holdings (especially premium tokens)
   • Active liquidity provision in valuable pools
   • Consistent yield farming participation
   • Accumulated pending rewards

Example agent with 100 He3 + 50 GPH/Y LP + 25 staked LP:
Resource: (100 × 100) = 10,000
LP: (50 × 40) = 2,000  
Farming: (25 × 40) = 1,000
Total: 13,000 points
"""

import time
from decimal import Decimal
from typing import Dict, Optional, List, Tuple
import os

from dipdup.context import HookContext
from starknet_py.contract import Contract
from starknet_py.net.full_node_client import FullNodeClient

from defi_space_indexer.models import Agent, AgentScore, AgentStake, Farm, GameSession, LiquidityPosition, Pair
from defi_space_indexer.utils import get_token_info

# Get the node URL from environment variables
RPC_URL = os.environ.get('NODE_URL', '') + '/' + os.environ.get('NODE_API_KEY', '')

# Token info cache to avoid repeated RPC calls
TOKEN_INFO_CACHE: Dict[str, Tuple[str, str, int]] = {}

# Token weights configuration (updated values as specified)
TOKEN_WEIGHTS = {
    # High value tokens
    'He3': 100,
    
    # Medium value tokens  
    'GPH': 50,
    'Y': 50,
    
    # Lower value tokens
    'GRP': 25,
    'Dy': 25,
    
    # Base tokens
    'wD': 5,
    'C': 5,
    'Nd': 5,
}

# LP Pool weights (20-50 depending on pool)
LP_POOL_WEIGHTS = {
    'He3/wD': 50,
    'He3/GPH': 45,
    'GPH/Y': 40,
    'GRP/Dy': 30,
    'wD/C': 20,
    'C/Nd': 20,
}

# Farm weights (match LP weights)
FARM_WEIGHTS = LP_POOL_WEIGHTS.copy()

# Standard ERC20 ABI for balance queries
ERC20_BALANCE_ABI = [
    {
        "name": "balance_of",
        "inputs": [
            {
                "type": "core::starknet::contract_address::ContractAddress",
                "name": "account"
            }
        ],
        "outputs": [
            {
                "type": "core::integer::u256"
            }
        ],
        "state_mutability": "view",
        "type": "function"
    }
]


async def get_cached_token_info(token_address: str) -> Tuple[str, str, int]:
    """Get token info with caching to avoid repeated RPC calls"""
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
    Calculate progression scores for agents based on their onchain state.
    
    Scoring Logic:
    - Resource Balances: Sum token balances (wallet + LP + farms) * token weights
    - LP Positions: Sum LP amounts (held + staked) * LP pool weights  
    - Farming Score: Sum (staked LP * farm weight) + (pending rewards * token weight)
    - Total Score: Resource + LP + Farming scores
    
    Processes ALL agents in ALL active game sessions.
    All values are properly normalized using token decimals.
    """
    ctx.logger.info("Starting agent progression score calculation for ALL agents")
    
    # Clear token info cache at start of each run to get fresh data
    TOKEN_INFO_CACHE.clear()
    
    # Get all agents
    agents = await Agent.all()
    
    current_time = int(time.time())
    
    ctx.logger.info(f"Processing {len(agents)} agents")
    
    for agent in agents:
        try:
            ctx.logger.info(f"Calculating score for agent {agent.address} in session {agent.session_address}")
            
            # Calculate scores by category (only within the agent's game session)
            resource_score = await calculate_resource_balance_score(ctx, agent.address, agent.session_address)
            lp_score = await calculate_lp_position_score(ctx, agent.address, agent.session_address)
            farming_score = await calculate_farming_score(ctx, agent.address, agent.session_address)
            
            total_score = resource_score + lp_score + farming_score
            
            # Create detailed breakdown
            score_breakdown = {
                'resource_balances': await get_resource_balance_breakdown(ctx, agent.address, agent.session_address),
                'lp_positions': await get_lp_position_breakdown(ctx, agent.address, agent.session_address),
                'farming_activities': await get_farming_breakdown(ctx, agent.address, agent.session_address),
                'calculation_timestamp': current_time,
            }
            
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
                    'score_breakdown': score_breakdown,
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
                agent_score.score_breakdown = score_breakdown
                agent_score.last_calculated_at = current_time
                agent_score.updated_at = current_time
                await agent_score.save()
            
            ctx.logger.info(f"🎯 FINAL SCORES for agent {agent.address}:")
            ctx.logger.info(f"   📊 Resource Balance Score: {resource_score}")
            ctx.logger.info(f"   💧 LP Position Score: {lp_score}")
            ctx.logger.info(f"   🚜 Farming Score: {farming_score}")
            ctx.logger.info(f"   🏆 TOTAL SCORE: {total_score}")
            
        except Exception as e:
            ctx.logger.error(f"Error calculating score for agent {agent.address}: {e}")
            continue

    # Execute SQL script for additional optimizations
    await ctx.execute_sql_script('calculate_agent_progression_scores')
    
    ctx.logger.info("Completed agent progression score calculation")


async def get_wallet_token_balance(agent_address: str, token_address: str) -> Decimal:
    """Get token balance from agent's wallet"""
    try:
        client = FullNodeClient(node_url=RPC_URL)
        contract = await Contract.from_address(address=token_address, provider=client, abi=ERC20_BALANCE_ABI)
        
        balance_result = await contract.functions['balance_of'].call(agent_address)
        balance = balance_result[0] if isinstance(balance_result, (list, tuple)) else balance_result
        
        balance_decimal = handle_u256_value(balance)
        if balance_decimal > 0:
            print(f"DEBUG: Found wallet balance for agent {agent_address}: {balance_decimal} of token {token_address}")
        
        return balance_decimal
    except Exception as e:
        print(f"ERROR: Failed to get wallet balance for agent {agent_address}, token {token_address}: {e}")
        return Decimal(0)


async def get_lp_token_balance(agent_address: str, lp_token_address: str) -> Decimal:
    """Get LP token balance from agent's wallet"""
    return await get_wallet_token_balance(agent_address, lp_token_address)


async def get_farm_staked_balance(agent_address: str, farm_address: str) -> Decimal:
    """Get staked balance from a farm contract"""
    try:
        print(f"DEBUG: Getting staked balance for agent {agent_address} from farm {farm_address}")
        client = FullNodeClient(node_url=RPC_URL)
        # Load farm ABI
        with open('defi_space_indexer/abi/farming_farm/cairo_abi.json', 'r') as f:
            import json
            farm_abi = json.load(f)
        
        contract = await Contract.from_address(address=farm_address, provider=client, abi=farm_abi)
        
        balance_result = await contract.functions['balance_of'].call(agent_address)
        balance = balance_result[0] if isinstance(balance_result, (list, tuple)) else balance_result
        
        staked_balance = handle_u256_value(balance)
        if staked_balance > 0:
            print(f"DEBUG: Found staked balance for agent {agent_address}: {staked_balance} in farm {farm_address}")
        
        return staked_balance
    except Exception as e:
        print(f"ERROR: Failed to get staked balance for agent {agent_address} from farm {farm_address}: {e}")
        return Decimal(0)


async def get_farm_pending_rewards(agent_address: str, farm_address: str) -> Dict[str, Decimal]:
    """Get pending rewards from a farm contract"""
    try:
        print(f"DEBUG: Getting pending rewards for agent {agent_address} from farm {farm_address}")
        client = FullNodeClient(node_url=RPC_URL)
        # Load farm ABI
        with open('defi_space_indexer/abi/farming_farm/cairo_abi.json', 'r') as f:
            import json
            farm_abi = json.load(f)
        
        contract = await Contract.from_address(address=farm_address, provider=client, abi=farm_abi)
        
        # Get reward tokens
        reward_tokens_result = await contract.functions['get_reward_tokens'].call()
        reward_tokens = reward_tokens_result[0] if isinstance(reward_tokens_result, (list, tuple)) else reward_tokens_result
        
        print(f"DEBUG: Found {len(reward_tokens)} reward tokens in farm {farm_address}: {[str(t) for t in reward_tokens]}")
        
        pending_rewards = {}
        
        # Get earned amount for each reward token
        for token_address in reward_tokens:
            try:
                earned_result = await contract.functions['earned'].call(agent_address, token_address)
                earned = earned_result[0] if isinstance(earned_result, (list, tuple)) else earned_result
                
                earned_amount = handle_u256_value(earned)
                
                if earned_amount > 0:
                    pending_rewards[str(token_address)] = earned_amount
                    print(f"DEBUG: Found pending reward for agent {agent_address}: {earned_amount} of token {token_address}")
            except Exception as reward_error:
                print(f"WARNING: Failed to get earned amount for token {token_address} in farm {farm_address}: {reward_error}")
                continue
        
        print(f"DEBUG: Total pending rewards for agent {agent_address} in farm {farm_address}: {len(pending_rewards)} tokens")
        return pending_rewards
    except Exception as e:
        print(f"ERROR: Failed to get pending rewards for agent {agent_address} from farm {farm_address}: {e}")
        return {}


async def calculate_resource_balance_score(ctx: HookContext, agent_address: str, session_address: str) -> Decimal:
    """
    Calculate resource balance score based on:
    - Direct token holdings in wallet
    - Token amounts in LP positions (token0 + token1) within the same game session
    - Single-sided farm deposits within the same game session
    Each multiplied by token weight
    """
    ctx.logger.info(f"Calculating resource balance score for agent {agent_address} in session {session_address}")
    total_score = Decimal(0)
    token_balances = {}
    
    try:
        # Get session to determine game_session_id
        session = await GameSession.get(address=session_address)
        game_session_id = session.game_session_index
        ctx.logger.info(f"Agent {agent_address} belongs to game session ID {game_session_id}")
        
        # Get all unique tokens from pairs and farms in the same game session
        unique_tokens = set()
        
        # Collect tokens from LP pairs in the same game session
        pairs = await Pair.filter(game_session_id=game_session_id)
        ctx.logger.info(f"Found {len(pairs)} pairs in game session {game_session_id}")
        for pair in pairs:
            unique_tokens.add(pair.token0_address)
            unique_tokens.add(pair.token1_address)
            ctx.logger.debug(f"Added tokens from pair {pair.address}: {pair.token0_symbol} ({pair.token0_address}), {pair.token1_symbol} ({pair.token1_address})")
        
        # Collect tokens from farms in the same game session (reward tokens)
        farms = await Farm.filter(game_session_id=game_session_id)
        ctx.logger.info(f"Found {len(farms)} farms in game session {game_session_id}")
        for farm in farms:
            if farm.reward_tokens:
                for token_addr in farm.reward_tokens:
                    unique_tokens.add(token_addr)
                ctx.logger.debug(f"Added reward tokens from farm {farm.address}: {farm.reward_tokens}")
        
        # Get wallet balances for all tokens
        ctx.logger.info(f"Checking wallet balances for {len(unique_tokens)} unique tokens")
        for token_address in unique_tokens:
            try:
                balance = await get_wallet_token_balance(agent_address, token_address)
                if balance > 0:
                    # Get token info to determine symbol
                    _, symbol, decimals = await get_cached_token_info(token_address)
                    
                    # Normalize balance by decimals
                    normalized_balance = balance / (Decimal(10) ** decimals)
                    token_balances[symbol] = token_balances.get(symbol, Decimal(0)) + normalized_balance
                    ctx.logger.info(f"Added wallet balance for {symbol}: {normalized_balance} (raw: {balance})")
                    
            except Exception as e:
                ctx.logger.warning(f"Error getting balance for token {token_address}: {e}")
                continue
        
        # Calculate LP token amounts (extract underlying tokens) - only from same game session
        lp_positions = await LiquidityPosition.filter(agent_address=agent_address)
        ctx.logger.info(f"Found {len(lp_positions)} LP positions for agent {agent_address}")
        
        session_lp_count = 0
        for position in lp_positions:
            try:
                pair = await Pair.get(address=position.pair_address)
                
                # Only include LP positions from the same game session
                if pair.game_session_id != game_session_id:
                    ctx.logger.debug(f"Skipping LP position {position.pair_address} - belongs to session {pair.game_session_id}, not {game_session_id}")
                    continue
                
                session_lp_count += 1
                ctx.logger.info(f"Processing LP position {position.pair_address} ({pair.token0_symbol}/{pair.token1_symbol}) - liquidity: {position.liquidity}")
                
                # Calculate share of pool
                if pair.total_supply > 0:
                    share = Decimal(str(position.liquidity)) / Decimal(str(pair.total_supply))
                    ctx.logger.debug(f"LP share: {share} ({position.liquidity}/{pair.total_supply})")
                    
                    # Get token0 amount
                    token0_amount = share * Decimal(str(pair.reserve0))
                    _, token0_symbol, token0_decimals = await get_cached_token_info(pair.token0_address)
                    normalized_token0 = token0_amount / (Decimal(10) ** token0_decimals)
                    token_balances[token0_symbol] = token_balances.get(token0_symbol, Decimal(0)) + normalized_token0
                    ctx.logger.info(f"Added LP token0 amount for {token0_symbol}: {normalized_token0}")
                    
                    # Get token1 amount
                    token1_amount = share * Decimal(str(pair.reserve1))
                    _, token1_symbol, token1_decimals = await get_cached_token_info(pair.token1_address)
                    normalized_token1 = token1_amount / (Decimal(10) ** token1_decimals)
                    token_balances[token1_symbol] = token_balances.get(token1_symbol, Decimal(0)) + normalized_token1
                    ctx.logger.info(f"Added LP token1 amount for {token1_symbol}: {normalized_token1}")
                    
            except Exception as e:
                ctx.logger.warning(f"Error processing LP position {position.pair_address}: {e}")
                continue
        
        ctx.logger.info(f"Processed {session_lp_count} LP positions from current game session")
        
        # Apply weights to calculate final score
        ctx.logger.info(f"Applying weights to {len(token_balances)} token balances")
        for symbol, balance in token_balances.items():
            weight = TOKEN_WEIGHTS.get(symbol, 10)  # Default low weight
            score = balance * Decimal(str(weight))
            total_score += score
            ctx.logger.info(f"Token {symbol}: balance={balance}, weight={weight}, score={score}")
        
        ctx.logger.info(f"Total resource balance score for agent {agent_address}: {total_score}")
        
    except Exception as e:
        ctx.logger.error(f"Error calculating resource balance score for {agent_address}: {e}")
    
    return total_score


async def calculate_lp_position_score(ctx: HookContext, agent_address: str, session_address: str) -> Decimal:
    """
    Calculate LP position score based on:
    - LP tokens held in wallet (only from same game session)
    - LP tokens staked in farms (only from same game session)
    Each multiplied by LP pool weight
    """
    ctx.logger.info(f"Calculating LP position score for agent {agent_address} in session {session_address}")
    total_score = Decimal(0)
    
    try:
        # Get session to determine game_session_id
        session = await GameSession.get(address=session_address)
        game_session_id = session.game_session_index
        ctx.logger.info(f"Agent {agent_address} belongs to game session ID {game_session_id}")
        
        # Get agent's LP positions
        lp_positions = await LiquidityPosition.filter(agent_address=agent_address)
        ctx.logger.info(f"Found {len(lp_positions)} LP positions for agent {agent_address}")
        
        for position in lp_positions:
            try:
                # Get pair info to determine pool type
                pair = await Pair.get(address=position.pair_address)
                
                # Only include LP positions from the same game session
                if pair.game_session_id != game_session_id:
                    continue
                
                # Create pool identifier for weight lookup
                pool_key = f"{pair.token0_symbol}/{pair.token1_symbol}"
                if pool_key not in LP_POOL_WEIGHTS:
                    pool_key = f"{pair.token1_symbol}/{pair.token0_symbol}"
                
                weight = LP_POOL_WEIGHTS.get(pool_key, 20)  # Default weight
                
                # Get wallet LP balance
                wallet_lp_balance = await get_lp_token_balance(agent_address, position.pair_address)
                
                # LP tokens typically have 18 decimals, but let's get the actual decimals
                try:
                    _, _, lp_decimals = await get_cached_token_info(position.pair_address)
                except Exception:
                    lp_decimals = 18  # Default for LP tokens
                
                # Calculate score: LP amount * pool weight
                normalized_balance = normalize_token_amount(wallet_lp_balance, lp_decimals)
                position_score = normalized_balance * Decimal(str(weight))
                total_score += position_score
                
            except Exception as e:
                ctx.logger.warning(f"Error processing LP position {position.pair_address}: {e}")
                continue
        
        # Also check for LP tokens staked in farms (only from same game session)
        stakes = await AgentStake.filter(agent_address=agent_address)
        ctx.logger.info(f"Found {len(stakes)} stakes for agent {agent_address}")
        
        session_stakes_count = 0
        for stake in stakes:
            try:
                farm = await Farm.get(address=stake.farm_address)
                
                # Only include farms from the same game session
                if farm.game_session_id != game_session_id:
                    ctx.logger.debug(f"Skipping stake in farm {stake.farm_address} - belongs to session {farm.game_session_id}, not {game_session_id}")
                    continue
                
                session_stakes_count += 1
                ctx.logger.info(f"Processing staked LP in farm {stake.farm_address}")
                
                # Get LP token info
                lp_token_address = farm.lp_token_address
                pair = await Pair.get(address=lp_token_address)
                
                pool_key = f"{pair.token0_symbol}/{pair.token1_symbol}"
                if pool_key not in LP_POOL_WEIGHTS:
                    pool_key = f"{pair.token1_symbol}/{pair.token0_symbol}"
                
                weight = LP_POOL_WEIGHTS.get(pool_key, 20)
                
                # Get staked amount from farm
                staked_balance = await get_farm_staked_balance(agent_address, stake.farm_address)
                
                # Get LP token decimals
                try:
                    _, _, lp_decimals = await get_cached_token_info(lp_token_address)
                except Exception:
                    lp_decimals = 18  # Default for LP tokens
                
                normalized_staked = normalize_token_amount(staked_balance, lp_decimals)
                staking_score = normalized_staked * Decimal(str(weight))
                total_score += staking_score
                ctx.logger.info(f"Added staked LP score: {normalized_staked} * {weight} = {staking_score}")
                
            except Exception as e:
                ctx.logger.warning(f"Error processing staked LP in farm {stake.farm_address}: {e}")
                continue
        
        ctx.logger.info(f"Processed {session_stakes_count} stakes from current game session")
        ctx.logger.info(f"Total LP position score for agent {agent_address}: {total_score}")
                
    except Exception as e:
        ctx.logger.error(f"Error calculating LP position score for {agent_address}: {e}")
    
    return total_score


async def calculate_farming_score(ctx: HookContext, agent_address: str, session_address: str) -> Decimal:
    """
    Calculate farming score based on:
    - Pending rewards multiplied by token weight (only from same game session farms)
    Note: Staked LP tokens are counted in LP position score, not here
    """
    ctx.logger.info(f"Calculating farming score for agent {agent_address} in session {session_address}")
    total_score = Decimal(0)
    
    try:
        # Get session to determine game_session_id
        session = await GameSession.get(address=session_address)
        game_session_id = session.game_session_index
        ctx.logger.info(f"Agent {agent_address} belongs to game session ID {game_session_id}")
        
        # Get agent's stakes
        stakes = await AgentStake.filter(agent_address=agent_address)
        ctx.logger.info(f"Found {len(stakes)} stakes for agent {agent_address}")
        
        session_rewards_count = 0
        total_rewards_processed = 0
        
        for stake in stakes:
            try:
                # Check if farm belongs to the same game session
                farm = await Farm.get(address=stake.farm_address)
                if farm.game_session_id != game_session_id:
                    ctx.logger.debug(f"Skipping farm {stake.farm_address} - belongs to session {farm.game_session_id}, not {game_session_id}")
                    continue
                
                session_rewards_count += 1
                ctx.logger.info(f"Processing pending rewards from farm {stake.farm_address}")
                
                # Calculate pending rewards score only
                pending_rewards = await get_farm_pending_rewards(agent_address, stake.farm_address)
                ctx.logger.info(f"Found {len(pending_rewards)} pending reward tokens in farm {stake.farm_address}")
                
                for token_address, reward_amount in pending_rewards.items():
                    try:
                        # Get token info to determine weight
                        _, symbol, decimals = await get_cached_token_info(token_address)
                        token_weight = TOKEN_WEIGHTS.get(symbol, 1)  # Default weight
                        
                        # Normalize reward amount
                        normalized_reward = normalize_token_amount(reward_amount, decimals)
                        reward_score = normalized_reward * Decimal(str(token_weight))
                        total_score += reward_score
                        total_rewards_processed += 1
                        
                        ctx.logger.info(f"Added reward score for {symbol}: {normalized_reward} * {token_weight} = {reward_score}")
                        
                    except Exception as e:
                        ctx.logger.warning(f"Error processing reward token {token_address}: {e}")
                        continue
                
            except Exception as e:
                ctx.logger.warning(f"Error processing stake {stake.farm_address}: {e}")
                continue
        
        ctx.logger.info(f"Processed {session_rewards_count} farms from current game session")
        ctx.logger.info(f"Total rewards processed: {total_rewards_processed}")
        ctx.logger.info(f"Total farming score for agent {agent_address}: {total_score}")
                
    except Exception as e:
        ctx.logger.error(f"Error calculating farming score for {agent_address}: {e}")
    
    return total_score


async def get_resource_balance_breakdown(ctx: HookContext, agent_address: str, session_address: str) -> Dict:
    """Get detailed breakdown of resource balance scoring"""
    breakdown = {
        'wallet_balances': {},
        'lp_token_amounts': {},
        'farm_deposits': {},
        'total_by_token': {},
        'scores_by_token': {},
    }
    
    try:
        # Get session to determine game_session_id
        session = await GameSession.get(address=session_address)
        game_session_id = session.game_session_index
        
        # Get wallet balances (only from same game session)
        unique_tokens = set()
        pairs = await Pair.filter(game_session_id=game_session_id)
        for pair in pairs:
            unique_tokens.add(pair.token0_address)
            unique_tokens.add(pair.token1_address)
        
        for token_address in unique_tokens:
            try:
                balance = await get_wallet_token_balance(agent_address, token_address)
                if balance > 0:
                    # Get token info from contract to ensure consistency
                    _, token_symbol, decimals = await get_cached_token_info(token_address)
                    normalized = normalize_token_amount(balance, decimals)
                    
                    breakdown['wallet_balances'][token_symbol] = {
                        'amount': str(normalized),
                        'decimals': decimals,
                        'raw_amount': str(balance),
                    }
                    
                    weight = TOKEN_WEIGHTS.get(token_symbol, 1)
                    breakdown['scores_by_token'][token_symbol] = str(normalized * weight)
            except Exception:
                continue
                
    except Exception as e:
        ctx.logger.error(f"Error in resource balance breakdown: {e}")
    
    return breakdown


async def get_lp_position_breakdown(ctx: HookContext, agent_address: str, session_address: str) -> Dict:
    """Get detailed breakdown of LP position scoring"""
    breakdown = {
        'wallet_positions': {},
        'staked_positions': {},
        'scores_by_pool': {},
    }
    
    try:
        # Get session to determine game_session_id
        session = await GameSession.get(address=session_address)
        game_session_id = session.game_session_index
        
        # Get LP positions (only from same game session)
        lp_positions = await LiquidityPosition.filter(agent_address=agent_address)
        
        for position in lp_positions:
            try:
                pair = await Pair.get(address=position.pair_address)
                
                # Only include LP positions from the same game session
                if pair.game_session_id != game_session_id:
                    continue
                
                pool_key = f"{pair.token0_symbol}/{pair.token1_symbol}"
                
                # Wallet LP balance
                wallet_balance = await get_lp_token_balance(agent_address, position.pair_address)
                
                # Get LP token decimals
                try:
                    _, _, lp_decimals = await get_cached_token_info(position.pair_address)
                except Exception:
                    lp_decimals = 18  # Default for LP tokens
                
                normalized_wallet = normalize_token_amount(wallet_balance, lp_decimals)
                
                breakdown['wallet_positions'][pool_key] = {
                    'liquidity': str(normalized_wallet),
                    'pair_address': position.pair_address,
                    'decimals': lp_decimals,
                }
                
                weight = LP_POOL_WEIGHTS.get(pool_key, 20)
                breakdown['scores_by_pool'][pool_key] = str(normalized_wallet * weight)
                
            except Exception as e:
                ctx.logger.warning(f"Error in LP breakdown for {position.pair_address}: {e}")
        
        # Get staked LP positions (only from same game session)
        stakes = await AgentStake.filter(agent_address=agent_address)
        for stake in stakes:
            try:
                farm = await Farm.get(address=stake.farm_address)
                
                # Only include farms from the same game session
                if farm.game_session_id != game_session_id:
                    continue
                
                pair = await Pair.get(address=farm.lp_token_address)
                pool_key = f"{pair.token0_symbol}/{pair.token1_symbol}"
                
                staked_balance = await get_farm_staked_balance(agent_address, stake.farm_address)
                
                # Get LP token decimals
                try:
                    _, _, lp_decimals = await get_cached_token_info(farm.lp_token_address)
                except Exception:
                    lp_decimals = 18  # Default for LP tokens
                
                normalized_staked = normalize_token_amount(staked_balance, lp_decimals)
                
                breakdown['staked_positions'][pool_key] = {
                    'staked_amount': str(normalized_staked),
                    'farm_address': stake.farm_address,
                    'decimals': lp_decimals,
                }
            except Exception:
                continue
                
    except Exception as e:
        ctx.logger.error(f"Error in LP position breakdown: {e}")
    
    return breakdown


async def get_farming_breakdown(ctx: HookContext, agent_address: str, session_address: str) -> Dict:
    """Get detailed breakdown of farming scoring"""
    breakdown = {
        'active_stakes': {},
        'pending_rewards': {},
        'scores_by_farm': {},
    }
    
    try:
        # Get session to determine game_session_id
        session = await GameSession.get(address=session_address)
        game_session_id = session.game_session_index
        
        # Get agent stakes (only from same game session)
        stakes = await AgentStake.filter(agent_address=agent_address)
        
        for stake in stakes:
            try:
                farm = await Farm.get(address=stake.farm_address)
                
                # Only include farms from the same game session
                if farm.game_session_id != game_session_id:
                    continue
                
                # Staked amount
                staked_balance = await get_farm_staked_balance(agent_address, stake.farm_address)
                
                # Get LP token decimals
                try:
                    _, _, lp_decimals = await get_cached_token_info(farm.lp_token_address)
                except Exception:
                    lp_decimals = 18  # Default for LP tokens
                
                normalized_staked = normalize_token_amount(staked_balance, lp_decimals)
                
                breakdown['active_stakes'][stake.farm_address] = {
                    'staked_amount': str(normalized_staked),
                    'lp_token': farm.lp_token_address,
                    'penalty_end_time': stake.penalty_end_time,
                    'decimals': lp_decimals,
                }
                
                # Pending rewards
                pending_rewards = await get_farm_pending_rewards(agent_address, stake.farm_address)
                if pending_rewards:
                    breakdown['pending_rewards'][stake.farm_address] = {}
                    for token_addr, amount in pending_rewards.items():
                        try:
                            _, symbol, decimals = await get_cached_token_info(token_addr)
                            normalized = normalize_token_amount(amount, decimals)
                            breakdown['pending_rewards'][stake.farm_address][symbol] = {
                                'amount': str(normalized),
                                'decimals': decimals,
                                'raw_amount': str(amount),
                            }
                        except Exception:
                            continue
                
            except Exception as e:
                ctx.logger.warning(f"Error in farming breakdown for {stake.farm_address}: {e}")
                
    except Exception as e:
        ctx.logger.error(f"Error in farming breakdown: {e}")
    
    return breakdown 