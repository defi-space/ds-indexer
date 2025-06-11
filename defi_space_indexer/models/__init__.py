from dipdup import fields
from dipdup.models import Model

from defi_space_indexer.models.amm_models import AmmFactory  # Core Models
from defi_space_indexer.models.amm_models import LiquidityEvent  # Event Models
from defi_space_indexer.models.amm_models import LiquidityEventType
from defi_space_indexer.models.amm_models import LiquidityPosition
from defi_space_indexer.models.amm_models import Pair
from defi_space_indexer.models.amm_models import SwapEvent
from defi_space_indexer.models.farms_models import AgentStake
from defi_space_indexer.models.farms_models import AgentStakeEvent  # Event Models
from defi_space_indexer.models.farms_models import Farm
from defi_space_indexer.models.farms_models import FarmFactory  # Core Models
from defi_space_indexer.models.farms_models import Reward
from defi_space_indexer.models.farms_models import Rewarder
from defi_space_indexer.models.farms_models import RewardEvent
from defi_space_indexer.models.farms_models import RewardEventType
from defi_space_indexer.models.farms_models import RewardPerAgent
from defi_space_indexer.models.farms_models import StakeEventType
from defi_space_indexer.models.faucet_models import ClaimEvent  # Event Models
from defi_space_indexer.models.faucet_models import ClaimEventType
from defi_space_indexer.models.faucet_models import Faucet
from defi_space_indexer.models.faucet_models import FaucetFactory  # Core Models
from defi_space_indexer.models.faucet_models import FaucetToken
from defi_space_indexer.models.faucet_models import WhitelistedUser
from defi_space_indexer.models.game_models import Agent
from defi_space_indexer.models.game_models import AgentScore
from defi_space_indexer.models.game_models import GameEvent  # Event Models
from defi_space_indexer.models.game_models import GameEventType
from defi_space_indexer.models.game_models import GameFactory  # Core Models
from defi_space_indexer.models.game_models import GameSession
from defi_space_indexer.models.game_models import UserDeposit

__all__ = [
    'Agent',
    'AgentScore',
    'AgentStake',
    # Farming Event Models
    'AgentStakeEvent',
    # AMM Core Models
    'AmmFactory',
    # Faucet Event Models
    'ClaimEvent',
    'ClaimEventType',
    'Farm',
    # Farming Core Models
    'FarmFactory',
    'Faucet',
    # Faucet Core Models
    'FaucetFactory',
    'FaucetToken',
    # Game Event Models
    'GameEvent',
    'GameEventType',
    # Game Core Models
    'GameFactory',
    'GameSession',
    # AMM Event Models
    'LiquidityEvent',
    'LiquidityEventType',
    'LiquidityPosition',
    'Pair',
    'Reward',
    'RewardEvent',
    'RewardEventType',
    'RewardPerAgent',
    'Rewarder',
    'StakeEventType',
    'SwapEvent',
    'UserDeposit',
    'WhitelistedUser',
]
