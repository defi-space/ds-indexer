from dipdup import fields
from dipdup.models import Model

from defi_space_indexer.models.amm_models import (
    # Core Models
    Factory,
    Pair,
    LiquidityPosition,
    # Event Models
    LiquidityEvent,
    LiquidityEventType,
    SwapEvent,
)

from defi_space_indexer.models.farms_models import (
    # Core Models
    FarmFactory,
    Farm,
    AgentStake,
    Reward,
    RewardPerAgent,
    Rewarder,
    # Event Models
    AgentStakeEvent,
    StakeEventType,
    RewardEvent,
    RewardEventType,
)

from defi_space_indexer.models.game_models import (
    # Core Models
    GameFactory,
    GameSession,
    StakeWindow,
    UserStake,
    Agent,
    # Event Models
    GameEvent,
    GameEventType,
)

from defi_space_indexer.models.faucet_models import (
    # Core Models
    FaucetFactory,
    Faucet,
    FaucetToken,
    WhitelistedUser,
    # Event Models
    ClaimEvent,
    ClaimEventType,
)

__all__ = [
    # AMM Core Models
    'Factory',
    'Pair',
    'LiquidityPosition',
    
    # AMM Event Models
    'LiquidityEvent',
    'LiquidityEventType',
    'SwapEvent',
    
    # Farming Core Models
    'FarmFactory',
    'Farm',
    'AgentStake',
    'Reward',
    'RewardPerAgent',
    'Rewarder',
    
    # Farming Event Models
    'AgentStakeEvent',
    'StakeEventType',
    'RewardEvent',
    'RewardEventType',
    
    # Game Core Models
    'GameFactory',
    'GameSession',
    'StakeWindow',
    'UserStake',
    'Agent',
    
    # Game Event Models
    'GameEvent',
    'GameEventType',
    
    # Faucet Core Models
    'FaucetFactory',
    'Faucet',
    'FaucetToken',
    'WhitelistedUser',
    
    # Faucet Event Models
    'ClaimEvent',
    'ClaimEventType',
]
