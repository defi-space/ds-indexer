from dipdup import fields
from dipdup.models import Model
from enum import Enum


class GameFactory(Model):
    """
    Represents a GameFactory contract that creates and manages game sessions.
    This is the top-level contract that controls the gaming protocol.
    
    Key responsibilities:
    - Creates new game sessions
    - Tracks total number of sessions
    - Manages protocol configuration
    - Maintains ownership and administrative settings
    
    Historical tracking:
    - Stores configuration changes in config_history
    - Tracks ownership transfers
    - Records game session implementations
    """
    address = fields.TextField(primary_key=True)  # ContractAddress
    num_of_sessions = fields.IntField()
    total_value_locked_usd = fields.BigIntField(null=True)  # Derived from session TVLs
    
    # Config with history
    owner = fields.TextField()  # Current owner
    game_session_class_hash = fields.TextField()  # Current implementation
    config_history = fields.JSONField()  # List of {field, old_value, new_value, timestamp}
    
    created_at = fields.BigIntField()
    updated_at = fields.BigIntField()


class GameSession(Model):
    """
    Represents a GameSession contract for token staking and reward distribution.
    Each session manages staking of tokens for different agents and distributes rewards to winners.
    
    Key responsibilities:
    - Manages token staking for agents
    - Handles reward distribution
    - Controls game lifecycle
    - Tracks staking metrics
    
    Differs from Reactor:
    - Uses competing stakes model vs yield farming
    - Distributes rewards to winners vs all stakers
    - Has defined game lifecycle vs continuous staking
    
    Relationships:
    - Created by and linked to GameFactory
    - Has many UserGameStakes
    - Has multiple staking windows
    """
    address = fields.TextField(primary_key=True)  # ContractAddress
    
    # Creation data (from GameSessionCreatedEvent)
    factory_address = fields.TextField()
    stake_token_address = fields.TextField()
    token_win_condition_address = fields.TextField()
    token_win_condition_threshold = fields.DecimalField(max_digits=100, decimal_places=0)
    session_index = fields.IntField()
    
    # Game configuration
    owner = fields.TextField()
    burn_fee_percentage = fields.BigIntField()
    platform_fee_percentage = fields.BigIntField()
    fee_recipient = fields.TextField()
    number_of_stake_windows = fields.IntField()
    number_of_agents = fields.IntField()
    
    # Current state
    is_suspended = fields.BooleanField(default=False)
    is_over = fields.BooleanField(default=False)
    winning_agent_index = fields.IntField(null=True)
    total_staked = fields.DecimalField(max_digits=100, decimal_places=0)
    current_window_index = fields.IntField(default=0)
    
    # Game results
    total_rewards = fields.DecimalField(max_digits=100, decimal_places=0, null=True)
    burn_fee_amount = fields.DecimalField(max_digits=100, decimal_places=0, null=True)
    platform_fee_amount = fields.DecimalField(max_digits=100, decimal_places=0, null=True)
    total_fees_amount = fields.DecimalField(max_digits=100, decimal_places=0, null=True)
    
    # Timestamps
    created_at = fields.BigIntField()
    updated_at = fields.BigIntField()
    ended_at = fields.BigIntField(null=True)
    
    # Config with history
    config_history = fields.JSONField()  # List of {field, old_value, new_value, timestamp}
    
    # Relationships
    factory: fields.ForeignKeyField[GameFactory] = fields.ForeignKeyField(
        'models.GameFactory', related_name='sessions'
    )


class StakeWindow(Model):
    """
    Represents a staking window in a game session.
    Each window defines a period when users can stake or unstake.
    
    Key responsibilities:
    - Defines staking time periods
    - Tracks window-specific metrics
    - Manages window lifecycle
    """
    id = fields.IntField(primary_key=True)
    session_address = fields.TextField()
    window_index = fields.IntField()
    
    start_time = fields.BigIntField()
    end_time = fields.BigIntField()
    is_active = fields.BooleanField()
    
    total_staked = fields.DecimalField(max_digits=100, decimal_places=0, default=0)
    
    created_at = fields.BigIntField()
    
    # Relationships
    session: fields.ForeignKeyField[GameSession] = fields.ForeignKeyField(
        'models.GameSession', related_name='stake_windows'
    )


class UserGameStake(Model):
    """
    Tracks a user's stake in a specific game session.
    Represents the current state of a user's staked tokens and potential rewards.
    
    Key responsibilities:
    - Tracks staked token amount per agent
    - Records claimed rewards
    - Manages agent selections
    
    Differs from UserStake:
    - Tracks agent selection vs generic staking
    - Rewards based on winning vs continuous distribution
    - Fixed windows vs continuous staking
    """
    id = fields.IntField(primary_key=True)
    session_address = fields.TextField()  # ContractAddress
    user_address = fields.TextField()  # ContractAddress
    agent_index = fields.IntField()
    
    # Current Position State
    staked_amount = fields.DecimalField(max_digits=100, decimal_places=0)
    claimed_rewards = fields.DecimalField(max_digits=100, decimal_places=0, default=0)
    
    # Timestamps
    created_at = fields.BigIntField()  # First stake timestamp
    updated_at = fields.BigIntField()  # Last action timestamp
    
    # Relationships
    session: fields.ForeignKeyField[GameSession] = fields.ForeignKeyField(
        'models.GameSession', related_name='user_stakes'
    )


class GameEventType(Enum):
    STAKE = "STAKE"
    UNSTAKE = "UNSTAKE"
    EMERGENCY_WITHDRAW = "EMERGENCY_WITHDRAW"
    REWARDS_CLAIMED = "REWARDS_CLAIMED"


class GameEvent(Model):
    """
    Records individual game-related events.
    Captures detailed staking, unstaking, and reward claiming events.
    
    Key responsibilities:
    - Records stake/unstake events
    - Tracks reward claims
    - Captures emergency withdrawals
    
    Used for:
    - User activity tracking
    - TVL calculations
    - Game analytics
    """
    id = fields.IntField(primary_key=True)
    transaction_hash = fields.TextField()
    created_at = fields.BigIntField()
    
    event_type = fields.EnumField(GameEventType)
    user_address = fields.TextField()
    
    # Fields for STAKE and UNSTAKE
    agent_index = fields.IntField(null=True)
    window_index = fields.IntField(null=True)
    amount = fields.DecimalField(max_digits=100, decimal_places=0)
    
    # Relationships
    session: fields.ForeignKeyField[GameSession] = fields.ForeignKeyField(
        'models.GameSession', related_name='game_events'
    )
    user_stake: fields.ForeignKeyField[UserGameStake] = fields.ForeignKeyField(
        'models.UserGameStake', related_name='events', null=True
    )