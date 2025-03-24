from dipdup import fields
from dipdup.models import Model
from enum import Enum

class Powerplant(Model):
    """
    Represents a Powerplant contract that manages and controls reactors.
    This is the top-level contract for the yield farming protocol.
    
    Key responsibilities:
    - Creates and manages farming reactors
    - Tracks total value locked across all reactors
    - Controls protocol-wide settings
    - Manages ownership and permissions
    
    Historical tracking:
    - Stores configuration changes in config_history
    - Tracks ownership transfers
    - Records reactor implementations
    
    Differs from Factory:
    - Manages yield farming vs trading
    - Creates reactors vs trading pairs
    - Focuses on staking vs swapping
    """
    address = fields.TextField(primary_key=True)  # ContractAddress
    
    reactor_count = fields.BigIntField()
    
    # Config with history
    owner = fields.TextField()
    reactor_class_hash = fields.TextField()
    config_history = fields.JSONField()  # List of {field, old_value, new_value, timestamp}
    
    created_at = fields.BigIntField()
    updated_at = fields.BigIntField()


class Reactor(Model):
    """
    Represents a Reactor contract that manages liquidity and rewards.
    Each reactor handles staking of specific LP tokens and distributes rewards.
    
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
    - Created by and linked to Powerplant
    - Has many AgentStakes
    - Distributes multiple reward tokens
    """
    address = fields.TextField(primary_key=True)  # ContractAddress
    
    # Creation data (from ReactorCreatedEvent)
    powerplant_address = fields.TextField()
    lp_token_address = fields.TextField()
    reactor_index = fields.IntField()
    
    # Current state
    owner = fields.TextField()
    total_staked = fields.DecimalField(max_digits=100, decimal_places=0)
    multiplier = fields.BigIntField()
    locked = fields.BooleanField()
    
    created_at = fields.BigIntField()
    updated_at = fields.BigIntField()
    
    # Config with history
    penalty_duration = fields.BigIntField()
    withdraw_penalty = fields.BigIntField()
    penalty_receiver = fields.TextField()
    authorized_rewarders = fields.JSONField()
    config_history = fields.JSONField()  # List of {field, old_value, new_value, timestamp}
    
    # Reward state
    active_rewards = fields.JSONField()  # Map<token, {rate, duration, finish, stored}>
    
    # Relationships
    powerplant: fields.ForeignKeyField[Powerplant] = fields.ForeignKeyField(
        'models.Powerplant', related_name='reactors'
    )


class AgentStake(Model):
    """
    Tracks an agent's stake in a specific reactor.
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
    reactor_address = fields.TextField()  # ContractAddress
    agent_address = fields.TextField()  # ContractAddress
    
    # Current Position State
    staked_amount = fields.DecimalField(max_digits=100, decimal_places=0)
    penalty_end_time = fields.BigIntField()
    
    # Reward State
    reward_per_token_paid = fields.JSONField()  # Map<ContractAddress, u256>
    rewards = fields.JSONField()  # Map<ContractAddress, u256>
    
    # Timestamps
    created_at = fields.BigIntField()  # First stake timestamp
    updated_at = fields.BigIntField()  # Last action timestamp
    
    # Relationships
    reactor: fields.ForeignKeyField[Reactor] = fields.ForeignKeyField(
        'models.Reactor', related_name='agent_stakes'
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
    staked_amount = fields.DecimalField(max_digits=100, decimal_places=0)
    penalty_amount = fields.DecimalField(max_digits=100, decimal_places=0, null=True)  # For withdrawals
    
    # Relationships
    reactor: fields.ForeignKeyField[Reactor] = fields.ForeignKeyField(
        'models.Reactor', related_name='stake_events'
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
    reward_amount = fields.DecimalField(max_digits=100, decimal_places=0)
    
    # Additional fields for REWARD_ADDED
    reward_rate = fields.DecimalField(max_digits=100, decimal_places=0, null=True)
    reward_duration = fields.BigIntField(null=True)
    period_finish = fields.BigIntField(null=True)
    
    # Relationships
    reactor: fields.ForeignKeyField[Reactor] = fields.ForeignKeyField(
        'models.Reactor', related_name='reward_events'
    )