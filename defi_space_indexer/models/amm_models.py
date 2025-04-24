from dipdup import fields
from dipdup.models import Model
from enum import Enum


class AmmFactory(Model):
    """
    Represents an AMM AmmFactory contract that creates and manages pairs.
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
    - Created by and linked to AmmFactory
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

    # Game integration
    game_session_id = fields.IntField()  # ID for game session integration

    created_at = fields.BigIntField()
    updated_at = fields.BigIntField()
    
    # Relationships
    factory: fields.ForeignKeyField[AmmFactory] = fields.ForeignKeyField(
        'models.AmmFactory', related_name='pairs'
    )


class LiquidityPosition(Model):
    """
    Tracks an agent's liquidity position in a specific pair.
    Represents the current state of an agent's LP tokens and their history.
    
    Key responsibilities:
    - Tracks current LP token balance
    - Records historical deposits/withdrawals
    - Calculates position value and returns
    
    Differs from LiquidityEvent:
    - Stores current position vs individual events
    - Maintains cumulative amounts vs single transactions
    - Tracks agent-specific metrics vs raw events
    
    Updated by:
    - Mint events (deposits)
    - Burn events (withdrawals)
    - Sync events (reserve updates)
    """
    id = fields.IntField(primary_key=True)
    pair_address = fields.TextField()  # ContractAddress
    agent_address = fields.TextField()  # ContractAddress
    
    # Current Position State
    liquidity = fields.DecimalField(max_digits=100, decimal_places=0)  # Current LP token balance
    
    # Historical Amounts
    deposits_token0 = fields.DecimalField(max_digits=100, decimal_places=0)  # Cumulative token0 deposits
    deposits_token1 = fields.DecimalField(max_digits=100, decimal_places=0)  # Cumulative token1 deposits
    withdrawals_token0 = fields.DecimalField(max_digits=100, decimal_places=0, null=True)  # Cumulative token0 withdrawals
    withdrawals_token1 = fields.DecimalField(max_digits=100, decimal_places=0, null=True)  # Cumulative token1 withdrawals
    
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
    - Agent activity tracking
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
    - Agent trading history
    - Market analysis
    """
    id = fields.IntField(primary_key=True)
    transaction_hash = fields.TextField()
    created_at = fields.BigIntField()  # Timestamp
    block_number = fields.BigIntField(null=True)  # Block number
    
    sender = fields.TextField()  # Address that initiated the swap
    to = fields.TextField(null=True)  # Address that received the output tokens (may be different from sender)
    amount0_in = fields.DecimalField(max_digits=100, decimal_places=0)
    amount1_in = fields.DecimalField(max_digits=100, decimal_places=0)
    amount0_out = fields.DecimalField(max_digits=100, decimal_places=0)
    amount1_out = fields.DecimalField(max_digits=100, decimal_places=0)
    
    # Analytics fields
    price_impact = fields.DecimalField(max_digits=100, decimal_places=18, null=True)  # Calculated price impact
    
    # Relationships
    pair: fields.ForeignKeyField[Pair] = fields.ForeignKeyField(
        'models.Pair', related_name='swaps'
    )