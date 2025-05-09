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
    owner = fields.TextField()  # Current owner
    game_session_class_hash = fields.TextField()  # Current implementation
    game_session_count = fields.IntField()  # Number of game sessions
    
    # Config with history
    config_history = fields.JSONField()  # List of {field, old_value, new_value, timestamp}
    
    # Lists
    game_sessions_list = fields.JSONField(default=list)  # Array of game session addresses
    
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
    
    Differs from Farm:
    - Uses competing stakes model vs yield farming
    - Distributes rewards to winners vs all stakers
    - Has defined game lifecycle vs continuous staking
    
    Relationships:
    - Created by and linked to GameFactory
    - Has many UserGameStakes
    - Has multiple staking windows
    """
    address = fields.TextField(primary_key=True)  # ContractAddress
    
    # Creation data
    game_factory = fields.TextField()  # Factory address
    user_stake_token_address = fields.TextField()
    token_win_condition_address = fields.TextField()
    token_win_condition_threshold = fields.DecimalField(max_digits=100, decimal_places=0)
    
    token_win_condition_name = fields.TextField()
    token_win_condition_symbol = fields.TextField()
    token_win_condition_decimals = fields.IntField()
    
    user_stake_token_name = fields.TextField()
    user_stake_token_symbol = fields.TextField()
    user_stake_token_decimals = fields.IntField()
    
    # Game configuration
    owner = fields.TextField()
    burn_fee_percentage = fields.BigIntField()
    platform_fee_percentage = fields.BigIntField()
    fee_recipient = fields.TextField()
    number_of_stake_windows = fields.IntField()
    number_of_agents = fields.IntField()
    
    # Current state
    game_suspended = fields.BooleanField(default=False)
    game_over = fields.BooleanField(default=False)
    winning_agent_index = fields.IntField(null=True)
    total_rewards = fields.DecimalField(max_digits=100, decimal_places=0, default=0)
    current_window_index = fields.IntField(null=True)  # Index of the current active window
    
    game_session_index = fields.IntField()
    # Lists
    stake_windows_list = fields.JSONField(default=list)  # Array of stake window indices
    agents_list = fields.JSONField(default=list)  # Array of agent addresses
    
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


class Agent(Model):
    """
    Represents an agent in a game session.
    Each agent can receive stakes from users and potentially win the game.
    
    Key responsibilities:
    - Tracks total stake amount
    - Maintains agent initialization status
    - Links to game session
    """
    address = fields.TextField()  # ContractAddress
    agent_index = fields.IntField()
    session_address = fields.TextField()
    total_staked = fields.DecimalField(max_digits=100, decimal_places=0, default=0)
    
    created_at = fields.BigIntField()
    updated_at = fields.BigIntField()
    
    # Relationships
    session: fields.ForeignKeyField[GameSession] = fields.ForeignKeyField(
        'models.GameSession', related_name='agents'
    )
    
    class Meta:
        unique_together = [('address', 'session_address')]


class StakeWindow(Model):
    """
    Represents a staking window in a game session.
    Each window defines a period when users can stake or unstake.
    
    Key responsibilities:
    - Defines staking time periods
    - Tracks window-specific metrics
    - Manages window lifecycle
    """
    index = fields.IntField()
    session_address = fields.TextField()
    
    start_time = fields.BigIntField()
    end_time = fields.BigIntField()
    is_active = fields.BooleanField(default=False)
    
    total_staked = fields.DecimalField(max_digits=100, decimal_places=0, default=0)
    
    created_at = fields.BigIntField()
    updated_at = fields.BigIntField()
    
    # Relationships
    session: fields.ForeignKeyField[GameSession] = fields.ForeignKeyField(
        'models.GameSession', related_name='stake_windows'
    )
    
    class Meta:
        unique_together = [('index', 'session_address')]


class UserStake(Model):
    """
    Tracks a user's stake in a specific game session.
    Represents the current state of a user's staked tokens and potential rewards.
    
    Key responsibilities:
    - Tracks staked token amount per agent
    - Records claimed rewards
    - Manages agent selections
    """
    user_address = fields.TextField()  # ContractAddress
    agent_index = fields.IntField()
    stake_window_index = fields.IntField()
    session_address = fields.TextField()  # ContractAddress
    
    # Current Position State
    amount = fields.DecimalField(max_digits=100, decimal_places=0)
    claimed_rewards = fields.DecimalField(max_digits=100, decimal_places=0, default=0)
    
    # Timestamps
    created_at = fields.BigIntField()  # First stake timestamp
    updated_at = fields.BigIntField()  # Last action timestamp
    
    # Relationships
    session: fields.ForeignKeyField[GameSession] = fields.ForeignKeyField(
        'models.GameSession', related_name='user_stakes'
    )
    
    class Meta:
        unique_together = [('user_address', 'agent_index', 'stake_window_index', 'session_address')]


class GameEventType(Enum):
    STAKE = "STAKE"
    UNSTAKE = "UNSTAKE"
    EMERGENCY_WITHDRAW = "EMERGENCY_WITHDRAW"
    REWARDS_CLAIMED = "REWARDS_CLAIMED"
    GAME_OVER = "GAME_OVER"
    GAME_SUSPENDED = "GAME_SUSPENDED"
    GAME_INITIALIZED = "GAME_INITIALIZED"


class GameEvent(Model):
    """
    Records individual game-related events.
    Captures detailed staking, unstaking, and reward claiming events.
    
    Key responsibilities:
    - Records stake/unstake events
    - Tracks reward claims
    - Captures emergency withdrawalscd 
    
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
    stake_window_index = fields.IntField(null=True)
    amount = fields.DecimalField(max_digits=100, decimal_places=0)
    
    # Relationships
    session: fields.ForeignKeyField[GameSession] = fields.ForeignKeyField(
        'models.GameSession', related_name='game_events'
    )