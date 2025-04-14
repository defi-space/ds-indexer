from dipdup import fields
from dipdup.models import Model


class Faucet(Model):
    """
    Represents a Faucet contract that distributes tokens to whitelisted users.
    This is the main contract that controls token distribution.
    
    Key responsibilities:
    - Manages whitelisted users
    - Controls token distribution
    - Tracks claim intervals
    - Maintains ownership settings
    
    Relationships:
    - Has many FaucetTokens (available tokens)
    - Has many WhitelistedUsers (users eligible for claims)
    """
    address = fields.TextField(primary_key=True)  # ContractAddress
    owner = fields.TextField()  # ContractAddress
    claim_interval = fields.BigIntField()  # Interval between claims
    
    # Game integration
    game_session_id = fields.IntField(null=True)  # ID for game session integration
    
    # Lists
    tokens_list = fields.JSONField(default=list)  # Array of token addresses
    
    created_at = fields.BigIntField()
    updated_at = fields.BigIntField()


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
    
    user_address = fields.TextField()  # User who claimed
    token_address = fields.TextField()  # Token that was claimed
    faucet_address = fields.TextField()  # Faucet contract address
    amount = fields.DecimalField(max_digits=100, decimal_places=0)  # Amount claimed
    
    # Relationships
    faucet: fields.ForeignKeyField[Faucet] = fields.ForeignKeyField(
        'models.Faucet', related_name='claims'
    )
    token: fields.ForeignKeyField[FaucetToken] = fields.ForeignKeyField(
        'models.FaucetToken', related_name='claims'
    )
    user: fields.ForeignKeyField[WhitelistedUser] = fields.ForeignKeyField(
        'models.WhitelistedUser', related_name='claims'
    ) 