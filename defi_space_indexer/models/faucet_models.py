from dipdup import fields
from dipdup.models import Model
from enum import Enum


class FaucetFactory(Model):
    """
    Represents a FaucetFactory contract that creates and manages faucets.
    This is the top-level contract that controls the faucet protocol.
    
    Key responsibilities:
    - Creates new faucet instances
    - Tracks total number of faucets
    - Manages protocol configuration
    - Maintains ownership and administrative settings
    
    Historical tracking:
    - Stores configuration changes in config_history
    - Tracks ownership transfers
    - Records faucet implementations
    
    Similar to FarmFactory and AMM Factory:
    - Creates and manages instances of specific contracts
    - Controls protocol-wide settings
    - Maintains ownership permissions
    """
    address = fields.TextField(primary_key=True)  # ContractAddress
    
    # Core data
    faucet_count = fields.IntField()
    
    # Config with history
    owner = fields.TextField()  # Current owner
    faucet_class_hash = fields.TextField()  # Current implementation
    config_history = fields.JSONField(default=list)  # List of {field, old_value, new_value, timestamp}
    
    created_at = fields.BigIntField()
    updated_at = fields.BigIntField()


class Faucet(Model):
    """
    Represents a Faucet contract that distributes tokens to whitelisted users.
    This is an instance created by the FaucetFactory that controls token distribution.
    
    Key responsibilities:
    - Manages whitelisted users
    - Controls token distribution
    - Tracks claim intervals
    - Maintains ownership settings
    
    Relationships:
    - Created by and linked to FaucetFactory
    - Has many FaucetTokens (available tokens)
    - Has many WhitelistedUsers (users eligible for claims)
    """
    address = fields.TextField(primary_key=True)  # ContractAddress
    
    # Creation data
    factory_address = fields.TextField()  # Address of factory that created this faucet
    faucet_index = fields.IntField()  # Index in the factory's list
    
    # Core configuration
    owner = fields.TextField()  # ContractAddress
    claim_interval = fields.TextField()  # Interval between claims, using TextField to handle large integers
    
    # Game integration
    game_session_id = fields.IntField(null=True)  # ID for game session integration
    
    # Lists
    tokens_list = fields.JSONField(default=list)  # Array of token addresses
    
    # Config with history
    config_history = fields.JSONField(default=list)  # List of {field, old_value, new_value, timestamp}
    
    created_at = fields.BigIntField()
    updated_at = fields.BigIntField()
    
    # Relationships
    factory: fields.ForeignKeyField[FaucetFactory] = fields.ForeignKeyField(
        'models.FaucetFactory', related_name='faucets'
    )


class FaucetToken(Model):
    """
    Represents a token distributed by the faucet.
    Manages token distribution settings and balances.
    
    Key responsibilities:
    - Tracks token availability
    - Manages claim amounts
    - Links to faucet contract
    """
    address = fields.TextField()  # ContractAddress
    faucet_address = fields.TextField()  # Address of the faucet this token belongs to
    
    # Token distribution settings
    amount = fields.DecimalField(max_digits=100, decimal_places=0)  # Total token amount
    claim_amount = fields.DecimalField(max_digits=100, decimal_places=0)  # Amount per claim
    claimed_amount = fields.DecimalField(max_digits=100, decimal_places=0, default=0)  # Total amount claimed by users
    
    created_at = fields.BigIntField()
    updated_at = fields.BigIntField()
    
    # Relationships
    faucet: fields.ForeignKeyField[Faucet] = fields.ForeignKeyField(
        'models.Faucet', related_name='tokens'
    )
    
    class Meta:
        unique_together = [('address', 'faucet_address')]


class WhitelistedUser(Model):
    """
    Represents a user eligible to claim tokens from the faucet.
    Tracks user status and claim history.
    
    Key responsibilities:
    - Maintains whitelist status
    - Tracks last claim timestamp
    - Links to faucet contract
    """
    address = fields.TextField()  # ContractAddress
    faucet_address = fields.TextField()  # Address of the faucet this user belongs to
    
    # User status and history
    is_whitelisted = fields.BooleanField(default=True)
    last_claim = fields.BigIntField(null=True)  # Timestamp of last claim
    
    created_at = fields.BigIntField()
    updated_at = fields.BigIntField()
    
    # Relationships
    faucet: fields.ForeignKeyField[Faucet] = fields.ForeignKeyField(
        'models.Faucet', related_name='users'
    )
    
    class Meta:
        unique_together = [('address', 'faucet_address')]


class ClaimEventType(Enum):
    CLAIM = "CLAIM"
    TOKEN_ADDED = "TOKEN_ADDED"
    TOKEN_REMOVED = "TOKEN_REMOVED"

class ClaimEvent(Model):
    """
    Records individual token claim events.
    Captures detailed claim data for historical tracking.
    
    Key responsibilities:
    - Records token claims
    - Tracks claim amounts
    - Maintains claim history
    
    Used for:
    - User activity tracking
    - Distribution analytics
    - Audit trail
    """
    id = fields.IntField(primary_key=True)
    transaction_hash = fields.TextField()
    created_at = fields.BigIntField()
    
    event_type = fields.EnumField(ClaimEventType)
    user_address = fields.TextField()  # User who claimed
    token_address = fields.TextField()  # Token that was claimed
    faucet_address = fields.TextField()  # Faucet contract address
    amount = fields.DecimalField(max_digits=100, decimal_places=0)  # Amount claimed
    
    # Relationships
    faucet: fields.ForeignKeyField[Faucet] = fields.ForeignKeyField(
        'models.Faucet', related_name='claims'
    )
    token: fields.ForeignKeyField[FaucetToken] = fields.ForeignKeyField(
        'models.FaucetToken', related_name='claims', null=True
    )
    user: fields.ForeignKeyField[WhitelistedUser] = fields.ForeignKeyField(
        'models.WhitelistedUser', related_name='claims', null=True
    ) 