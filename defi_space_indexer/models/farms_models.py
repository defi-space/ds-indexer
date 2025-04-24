from dipdup import fields
from dipdup.models import Model
from enum import Enum

class FarmFactory(Model):
    """
    Represents a FarmFactory contract that manages and controls farms.
    This is the top-level contract for the yield farming protocol.
    
    Key responsibilities:
    - Creates and manages farming reactors
    - Tracks total value locked across all farms
    - Controls protocol-wide settings
    - Manages ownership and permissions
    
    Historical tracking:
    - Stores configuration changes in config_history
    - Tracks ownership transfers
    - Records farm implementations
    
    Differs from Factory:
    - Manages yield farming vs trading
    - Creates farms vs trading pairs
    - Focuses on staking vs swapping
    """
    address = fields.TextField(primary_key=True)  # ContractAddress
    
    farm_count = fields.BigIntField()
    
    # Config with history
    owner = fields.TextField()
    farm_class_hash = fields.TextField()
    config_history = fields.JSONField()  # List of {field, old_value, new_value, timestamp}
    
    created_at = fields.BigIntField()
    updated_at = fields.BigIntField()


class Farm(Model):
    """
    Represents a Farm contract that manages liquidity and rewards.
    Each farm handles staking of specific LP tokens and distributes rewards.
    
    Key responsibilities:
    - Manages LP token staking
    - Handles reward distribution
    - Controls penalty mechanisms
    - Tracks staking metrics
    
    Differs from Pair:
    - Handles staking vs trading
    - Manages rewards vs swaps
    - Uses penalties vs fees
    
    Relationships:
    - Created by and linked to FarmFactory
    - Has many AgentStakes
    - Distributes multiple reward tokens
    """
    address = fields.TextField(primary_key=True)  # ContractAddress
    
    # Creation data (from FarmCreatedEvent)
    factory_address = fields.TextField()
    lp_token_address = fields.TextField()
    farm_index = fields.IntField()
    
    # Current state
    owner = fields.TextField()
    total_staked = fields.TextField()  # Changed from DecimalField to TextField
    multiplier = fields.TextField()
    
    created_at = fields.BigIntField()
    updated_at = fields.BigIntField()
    
    # Config with history
    penalty_duration = fields.TextField()
    withdraw_penalty = fields.TextField()
    penalty_receiver = fields.TextField()
    authorized_rewarders = fields.JSONField()
    config_history = fields.JSONField()  # List of {field, old_value, new_value, timestamp}
    
    # Game integration
    game_session_id = fields.TextField()
    
    # Reward state
    active_rewards = fields.JSONField()  # Map<token, {rate, duration, finish, stored}>
    reward_tokens = fields.JSONField(default=list)  # List of reward token addresses
    
    # Relationships
    factory: fields.ForeignKeyField[FarmFactory] = fields.ForeignKeyField(
        'models.FarmFactory', related_name='farms'
    )


class AgentStake(Model):
    """
    Tracks an agent's stake in a specific farm.
    Represents the current state of an agent's staked LP tokens and rewards.
    
    Key responsibilities:
    - Tracks staked LP token amount
    - Manages penalty timeframes
    - Records earned rewards
    - Calculates claimable rewards
    
    Differs from LiquidityPosition:
    - Handles staking vs liquidity
    - Tracks rewards vs fees
    - Manages penalties vs shares
    
    Updated by:
    - Deposit events (staking)
    - Withdraw events (unstaking)
    - Harvest events (claiming)
    """
    id = fields.IntField(primary_key=True)
    farm_address = fields.TextField()  # ContractAddress
    agent_address = fields.TextField()  # ContractAddress
    
    # Current Position State
    staked_amount = fields.TextField()  # Changed from DecimalField to TextField
    penalty_end_time = fields.BigIntField()
    
    # Reward State
    reward_per_token_paid = fields.JSONField()  # Map<ContractAddress, u256>
    rewards = fields.JSONField()  # Map<ContractAddress, u256>
    
    # Timestamps
    created_at = fields.BigIntField()  # First stake timestamp
    updated_at = fields.BigIntField()  # Last action timestamp
    
    # Relationships
    farm: fields.ForeignKeyField[Farm] = fields.ForeignKeyField(
        'models.Farm', related_name='agent_stakes'
    )
    
    class Meta:
        unique_together = [('farm_address', 'agent_address')]


class Reward(Model):
    """
    Represents a reward token configuration for a farm.
    Manages the distribution settings and current state for a specific reward token.
    
    Key responsibilities:
    - Tracks reward rate and duration
    - Manages unallocated rewards
    - Controls reward distribution timing
    - Stores cumulative reward calculations
    """
    id = fields.IntField(primary_key=True)
    address = fields.TextField()  # Reward token address
    farm_address = fields.TextField()  # Farm this reward belongs to
    
    # Reward configuration
    unallocated_rewards = fields.TextField()
    rewards_duration = fields.TextField()
    period_finish = fields.TextField()
    reward_rate = fields.TextField()
    last_update_time = fields.BigIntField()
    reward_per_token_stored = fields.TextField()
    decimals = fields.IntField()
    
    created_at = fields.BigIntField()
    updated_at = fields.BigIntField()
    
    # Relationships
    farm: fields.ForeignKeyField[Farm] = fields.ForeignKeyField(
        'models.Farm', related_name='rewards'
    )


class RewardPerAgent(Model):
    """
    Tracks the rewards due to a specific agent for a specific token.
    Links agents, farms, and reward tokens together with current reward state.
    
    Key responsibilities:
    - Tracks pending rewards by token and agent
    - Manages reward debt (reward_per_token_paid)
    - Enables efficient reward claiming
    """
    id = fields.IntField(primary_key=True)
    agent_address = fields.TextField()  # Agent address
    reward_token_address = fields.TextField()  # Reward token address
    farm_address = fields.TextField()  # Farm address
    
    # Reward state
    pending_rewards = fields.TextField()  # Changed from DecimalField to TextField
    reward_per_token_paid = fields.TextField()  # Changed from DecimalField to TextField
    
    created_at = fields.BigIntField()
    updated_at = fields.BigIntField()
    
    # Relationships
    agent_stake: fields.ForeignKeyField[AgentStake] = fields.ForeignKeyField(
        'models.AgentStake', related_name='reward_states'
    )
    reward: fields.ForeignKeyField[Reward] = fields.ForeignKeyField(
        'models.Reward', related_name='agent_rewards'
    )
    
    class Meta:
        unique_together = [('agent_address', 'reward_token_address', 'farm_address')]


class Rewarder(Model):
    """
    Represents an authorized rewarder for a farm.
    Controls permission to add rewards to farms.
    
    Key responsibilities:
    - Tracks authorization status
    - Manages reward permission
    """
    id = fields.IntField(primary_key=True)
    address = fields.TextField()  # Rewarder address
    farm_address = fields.TextField()  # Farm address
    is_authorized = fields.BooleanField(default=False)
    
    created_at = fields.BigIntField()
    updated_at = fields.BigIntField()
    
    # Relationships
    farm: fields.ForeignKeyField[Farm] = fields.ForeignKeyField(
        'models.Farm', related_name='rewarders'
    )


class StakeEventType(Enum):
    DEPOSIT = "DEPOSIT"
    WITHDRAW = "WITHDRAW"

class AgentStakeEvent(Model):
    """
    Records individual stake/unstake events.
    Captures raw staking event data for historical tracking.
    
    Key responsibilities:
    - Records deposit/withdraw events
    - Tracks penalty applications
    - Maintains staking history
    
    Differs from AgentStake:
    - Stores individual events vs current state
    - Records raw amounts vs cumulative totals
    - Tracks penalties per action vs timeframes
    
    Used for:
    - Historical analysis
    - Agent activity tracking
    - TVL calculations
    - Position updates
    """
    id = fields.IntField(primary_key=True)
    transaction_hash = fields.TextField()
    created_at = fields.BigIntField()
    
    event_type = fields.EnumField(StakeEventType)
    agent_address = fields.TextField()
    staked_amount = fields.TextField()  # Changed from DecimalField to TextField
    penalty_amount = fields.TextField(null=True)  # Changed from DecimalField to TextField
    
    # Relationships
    farm: fields.ForeignKeyField[Farm] = fields.ForeignKeyField(
        'models.Farm', related_name='stake_events'
    )
    stake: fields.ForeignKeyField[AgentStake] = fields.ForeignKeyField(
        'models.AgentStake', related_name='events'
    )


class RewardEventType(Enum):
    HARVEST = "HARVEST"
    REWARD_ADDED = "REWARD_ADDED"

class RewardEvent(Model):
    """
    Records reward-related events (harvests and reward additions).
    Captures detailed reward distribution and claiming data.
    
    Key responsibilities:
    - Records reward claims (harvests)
    - Tracks reward additions
    - Monitors distribution rates
    
    Differs from StakeEvent:
    - Focuses on rewards vs stakes
    - Tracks token distributions vs positions
    - Handles multiple reward tokens
    
    Used for:
    - APR calculations
    - Reward distribution tracking
    - Agent earnings history
    - Protocol metrics
    """
    id = fields.IntField(primary_key=True)
    transaction_hash = fields.TextField()
    created_at = fields.BigIntField()

    event_type = fields.EnumField(RewardEventType)
    agent_address = fields.TextField(null=True)  # For harvests
    reward_token = fields.TextField()
    reward_amount = fields.TextField()  # Changed from DecimalField to TextField
    
    # Additional fields for REWARD_ADDED
    reward_rate = fields.TextField(null=True)  # Changed from DecimalField to TextField
    reward_duration = fields.TextField(null=True)  # Changed from BigIntField to TextField
    period_finish = fields.TextField(null=True)  # Changed from BigIntField to TextField
    
    # Relationships
    farm: fields.ForeignKeyField[Farm] = fields.ForeignKeyField(
        'models.Farm', related_name='reward_events'
    )