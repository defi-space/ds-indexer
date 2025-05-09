from starknet_py.net.client import Client
from starknet_py.net.models import StarknetChainId
from starknet_py.net.full_node_client import FullNodeClient
from starknet_py.contract import Contract
import os
from logging import getLogger

logger = getLogger(__name__)

# Get the node URL from environment variables
RPC_URL = os.environ.get('NODE_URL', '') + '/' + os.environ.get('NODE_API_KEY', '')

async def get_token_info(address: str) -> tuple:
    """
    Get token name, symbol, and decimals for the given token address.
    
    Args:
        address: Token contract address in hex format (0x...)
        
    Returns:
        tuple: (name, symbol, decimals) of the token
    """
    try:
        # Create a client to interact with Starknet
        client = FullNodeClient(node_url=RPC_URL)

        logger.info(f"Trying token {address}")
        contract = await Contract.from_address(address=address, provider=client)
        
        name_result = await contract.functions["name"].call()
        symbol_result = await contract.functions["symbol"].call()
        decimals_result = await contract.functions["decimals"].call()
        
        return name_result[0], symbol_result[0], decimals_result[0]
            
    except Exception as e:
        logger.error(f"Error getting token info for {address}: {str(e)}", exc_info=True)
        return "Unknown", "UNK", 18  # Default to 18 decimals if there's an error