from enum import Enum

from dipdup import fields
from dipdup.models import Model


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
    Represents a GameSession contract for token deposit and reward distribution.
    Each session manages deposits of tokens for different agents and distributes rewards to winners.

    Key responsibilities:
    - Manages token deposits for agents
    - Handles reward distribution
    - Controls game lifecycle
    - Tracks deposit metrics and scores

    Differs from Farm:
    - Uses competing deposits model vs yield farming
    - Distributes rewards to winners vs all stakers
    - Has defined game lifecycle vs continuous staking

    Relationships:
    - Created by and linked to GameFactory
    - Has many UserDeposits
    - Has multiple agents
    """

    address = fields.TextField(primary_key=True)  # ContractAddress

    # Creation data
    game_factory = fields.TextField()  # Factory address
    user_deposit_token_address = fields.TextField()  # Changed from user_stake_token_address
    token_win_condition_address = fields.TextField()
    token_win_condition_threshold = fields.DecimalField(max_digits=100, decimal_places=0)

    token_win_condition_name = fields.TextField()
    token_win_condition_symbol = fields.TextField()
    token_win_condition_decimals = fields.IntField()

    user_deposit_token_name = fields.TextField()  # Changed from user_stake_token_name
    user_deposit_token_symbol = fields.TextField()  # Changed from user_stake_token_symbol
    user_deposit_token_decimals = fields.IntField()  # Changed from user_stake_token_decimals

    # Game configuration
    owner = fields.TextField()
    burn_fee_percentage = fields.BigIntField()
    platform_fee_percentage = fields.BigIntField()
    fee_recipient = fields.TextField()
    number_of_agents = fields.IntField()

    # Game timing
    game_start_timestamp = fields.BigIntField()
    game_end_timestamp = fields.BigIntField(null=True)

    # Current state
    game_suspended = fields.BooleanField(default=False)
    game_over = fields.BooleanField(default=False)
    winning_agent_index = fields.IntField(null=True)
    total_rewards = fields.DecimalField(max_digits=100, decimal_places=0, default=0)

    game_session_index = fields.IntField()
    # Lists
    agents_list = fields.JSONField(default=list)  # Array of agent addresses

    # Timestamps
    created_at = fields.BigIntField()
    updated_at = fields.BigIntField()
    ended_at = fields.BigIntField(null=True)

    # Config with history
    config_history = fields.JSONField()  # List of {field, old_value, new_value, timestamp}

    # Relationships
    factory: fields.ForeignKeyField[GameFactory] = fields.ForeignKeyField('models.GameFactory', related_name='sessions')


class Agent(Model):
    """
    Represents an agent in a game session.
    Each agent can receive deposits from users and potentially win the game.

    Key responsibilities:
    - Tracks total deposit amount
    - Tracks total score
    - Maintains agent initialization status
    - Links to game session
    """

    address = fields.TextField()  # ContractAddress
    agent_index = fields.IntField()
    session_address = fields.TextField()
    total_deposited = fields.DecimalField(max_digits=100, decimal_places=0, default=0)
    total_score = fields.DecimalField(max_digits=100, decimal_places=0, default=0)

    created_at = fields.BigIntField()
    updated_at = fields.BigIntField()

    # Relationships
    session: fields.ForeignKeyField[GameSession] = fields.ForeignKeyField('models.GameSession', related_name='agents')

    class Meta:
        unique_together = [('address', 'session_address')]


class UserDeposit(Model):
    """
    Tracks a user's deposit in a specific game session.
    Represents the current state of a user's deposited tokens and score.

    Key responsibilities:
    - Tracks deposited token amount per agent
    - Records accumulated score over time
    - Manages score calculations
    """

    user_address = fields.TextField()  # ContractAddress
    agent_index = fields.IntField()
    session_address = fields.TextField()  # ContractAddress

    # Current Position State
    amount = fields.DecimalField(max_digits=100, decimal_places=0)
    accumulated_score = fields.DecimalField(max_digits=100, decimal_places=0, default=0)
    last_score_update = fields.BigIntField()

    # Timestamps
    created_at = fields.BigIntField()  # First deposit timestamp
    updated_at = fields.BigIntField()  # Last action timestamp

    # Relationships
    session: fields.ForeignKeyField[GameSession] = fields.ForeignKeyField(
        'models.GameSession', related_name='user_deposits'
    )

    class Meta:
        unique_together = [('user_address', 'agent_index', 'session_address')]


class GameEventType(Enum):
    USER_DEPOSITED = 'USER_DEPOSITED'
    EMERGENCY_WITHDRAW = 'EMERGENCY_WITHDRAW'
    REWARDS_CLAIMED = 'REWARDS_CLAIMED'
    GAME_OVER = 'GAME_OVER'
    GAME_SUSPENDED = 'GAME_SUSPENDED'
    GAME_INITIALIZED = 'GAME_INITIALIZED'


class GameEvent(Model):
    """
    Records individual game-related events.
    Captures detailed deposit, and reward claiming events.

    Key responsibilities:
    - Records deposit events
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

    # Fields for USER_DEPOSITED
    agent_index = fields.IntField(null=True)
    amount = fields.DecimalField(max_digits=100, decimal_places=0)
    old_score = fields.DecimalField(max_digits=100, decimal_places=0, null=True)
    new_score = fields.DecimalField(max_digits=100, decimal_places=0, null=True)

    # Relationships
    session: fields.ForeignKeyField[GameSession] = fields.ForeignKeyField(
        'models.GameSession', related_name='game_events'
    )
