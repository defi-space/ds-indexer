from dipdup import fields
from dipdup.models import Model
from enum import Enum


class Factory(Model):
    """
    Represents an AMM Factory contract that creates and manages pairs.
    This is the top-level contract that controls the entire AMM protocol.
    
    Key responsibilities:
    - Creates new trading pairs
    - Tracks total number of pairs and TVL
    - Manages protocol configuration (fees, implementation)
    - Maintains ownership and administrative settings
    
    Historical tracking:
    - Stores configuration changes in config_history
    - Tracks ownership transfers
    - Records fee receiver updates
    """
    address = fields.TextField(primary_key=True)  # ContractAddress
    num_of_pairs = fields.IntField()
    total_value_locked_usd = fields.BigIntField(null=True)  # Derived from pair TVLs
    
    # Config with history
    owner = fields.TextField()  # Current owner
    fee_to = fields.TextField()  # Current fee receiver
    pair_contract_class_hash = fields.TextField()  # Current implementation
    config_history = fields.JSONField()  # List of {field, old_value, new_value, timestamp}
    
    created_at = fields.BigIntField()
    updated_at = fields.BigIntField()


class Pair(Model):
    """
    Represents an AMM Pair contract for token swaps.
    Each pair manages a pool of two tokens and enables trading between them.
    
    Key responsibilities:
    - Manages token reserves and liquidity
    - Handles swaps between tokens
    - Tracks price data and TWAP
    - Calculates fees and rewards
    
    Differs from PairEvent:
    - Stores current state vs historical events
    - Maintains live metrics vs event logs
    - Handles active trading vs historical records
    
    Relationships:
    - Created by and linked to Factory
    - Has many LiquidityPositions
    - Can be used in farming Reactors
    """
    address = fields.TextField(primary_key=True)  # ContractAddress
    
    # Creation data (from PairCreatedEvent)
    factory_address = fields.TextField()
    token0_address = fields.TextField()
    token1_address = fields.TextField()
    
    # Current state
    reserve0 = fields.DecimalField(max_digits=100, decimal_places=0)
    reserve1 = fields.DecimalField(max_digits=100, decimal_places=0)
    total_supply = fields.DecimalField(max_digits=100, decimal_places=0)
    klast = fields.DecimalField(max_digits=100, decimal_places=0)
    
    # TWAP data
    price_0_cumulative_last = fields.BigIntField()
    price_1_cumulative_last = fields.BigIntField()
    block_timestamp_last = fields.BigIntField()
    
    # Derived Metrics
    token0_price = fields.BigIntField(null=True)
    token1_price = fields.BigIntField(null=True)
    volume_24h = fields.BigIntField(null=True)
    tvl_usd = fields.BigIntField(null=True)
    apy_24h = fields.BigIntField(null=True)
    accumulated_fees_token0 = fields.BigIntField(null=True)
    accumulated_fees_token1 = fields.BigIntField(null=True)

    created_at = fields.BigIntField()
    updated_at = fields.BigIntField()
    
    # Relationships
    factory: fields.ForeignKeyField[Factory] = fields.ForeignKeyField(
        'models.Factory', related_name='pairs'
    )


class LiquidityPosition(Model):
    """
    Tracks a user's liquidity position in a specific pair.
    Represents the current state of a user's LP tokens and their history.
    
    Key responsibilities:
    - Tracks current LP token balance
    - Records historical deposits/withdrawals
    - Calculates position value and returns
    
    Differs from LiquidityEvent:
    - Stores current position vs individual events
    - Maintains cumulative amounts vs single transactions
    - Tracks user-specific metrics vs raw events
    
    Updated by:
    - Mint events (deposits)
    - Burn events (withdrawals)
    - Sync events (reserve updates)
    """
    id = fields.IntField(primary_key=True)
    pair_address = fields.TextField()  # ContractAddress
    user_address = fields.TextField()  # ContractAddress
    
    # Current Position State
    liquidity = fields.DecimalField(max_digits=100, decimal_places=0)  # Current LP token balance
    
    # Historical Amounts
    deposits_token0 = fields.DecimalField(max_digits=100, decimal_places=0)  # Cumulative token0 deposits
    deposits_token1 = fields.DecimalField(max_digits=100, decimal_places=0)  # Cumulative token1 deposits
    withdrawals_token0 = fields.DecimalField(max_digits=100, decimal_places=0, null=True)  # Cumulative token0 withdrawals
    withdrawals_token1 = fields.DecimalField(max_digits=100, decimal_places=0, null=True)  # Cumulative token1 withdrawals
    
    # Derived metrics
    usd_value = fields.BigIntField(null=True)  # Current position value in USD
    apy_earned = fields.BigIntField(null=True)  # Historical APY earned
    
    # Timestamps
    created_at = fields.BigIntField()  # First deposit timestamp
    updated_at = fields.BigIntField()  # Last action timestamp
    
    # Relationships
    pair: fields.ForeignKeyField[Pair] = fields.ForeignKeyField(
        'models.Pair', related_name='liquidity_positions'
    )


class LiquidityEventType(Enum):
    MINT = "MINT"
    BURN = "BURN"

class LiquidityEvent(Model):
    """
    Records individual liquidity provision/removal events.
    Captures raw event data for historical tracking and analysis.
    
    Key responsibilities:
    - Records mint/burn events
    - Tracks individual transactions
    - Maintains event history
    
    Differs from LiquidityPosition:
    - Stores individual events vs current state
    - Records raw amounts vs cumulative totals
    - Maintains complete history vs latest position
    
    Used for:
    - Historical analysis
    - User activity tracking
    - Volume calculations
    - Position updates
    """
    id = fields.IntField(primary_key=True)
    transaction_hash = fields.TextField()
    created_at = fields.BigIntField()
    
    event_type = fields.EnumField(LiquidityEventType)
    sender = fields.TextField()
    amount0 = fields.DecimalField(max_digits=100, decimal_places=0)
    amount1 = fields.DecimalField(max_digits=100, decimal_places=0)
    liquidity = fields.DecimalField(max_digits=100, decimal_places=0)

    # Relationships
    pair: fields.ForeignKeyField[Pair] = fields.ForeignKeyField(
        'models.Pair', related_name='liquidity_events'
    )
    position: fields.ForeignKeyField[LiquidityPosition] = fields.ForeignKeyField(
        'models.LiquidityPosition', related_name='events'
    )

class SwapEvent(Model):
    """
    Records individual swap events.
    Captures detailed swap data for analysis and volume tracking.
    
    Key responsibilities:
    - Records token swap events
    - Tracks trade amounts and direction
    - Enables volume calculations
    
    Differs from Pair model:
    - Stores individual trades vs current state
    - Records historical data vs live metrics
    - Focuses on swap activity vs overall pair state
    
    Used for:
    - Volume calculations
    - Price impact analysis
    - User trading history
    - Market analysis
    """
    id = fields.IntField(primary_key=True)
    transaction_hash = fields.TextField()
    created_at = fields.BigIntField()
    
    sender = fields.TextField()
    amount0_in = fields.DecimalField(max_digits=100, decimal_places=0)
    amount1_in = fields.DecimalField(max_digits=100, decimal_places=0)
    amount0_out = fields.DecimalField(max_digits=100, decimal_places=0)
    amount1_out = fields.DecimalField(max_digits=100, decimal_places=0)

    
    # Relationships
    pair: fields.ForeignKeyField[Pair] = fields.ForeignKeyField(
        'models.Pair', related_name='swaps'
    )