import os
from logging import getLogger

from starknet_py.contract import Contract
from starknet_py.net.full_node_client import FullNodeClient

logger = getLogger(__name__)

# Get the node URL from environment variables
RPC_URL = os.environ.get('NODE_URL', '') + '/' + os.environ.get('NODE_API_KEY', '')


def felt_to_string(felt: int) -> str:
    """Convert a felt to a string.

    Args:
        felt: The felt value to convert

    Returns:
        str: The string representation of the felt
    """
    length = 31  # Maximum length of characters stored in a felt
    felt_bytes = felt.to_bytes(length, byteorder='big')
    # Trim null bytes and decode
    return felt_bytes.decode('utf-8').strip('\x00')


async def get_token_info(address: str) -> tuple:
    """
    Get token name, symbol, and decimals for the given token address.
    Handles both ByteArray and felt252 return types for name and symbol.

    Args:
        address: Token contract address in hex format (0x...)

    Returns:
        tuple: (name, symbol, decimals) of the token
    """
    try:
        # Create a client to interact with Starknet
        client = FullNodeClient(node_url=RPC_URL)

        logger.info(f'Trying token {address}')
        contract = await Contract.from_address(address=address, provider=client)

        # Get name - handle both ByteArray and felt252 return types
        try:
            name_result = await contract.functions['name'].call()
            name = name_result[0]
            # If name is an integer (felt252), convert it to string
            if isinstance(name, int):
                name = felt_to_string(name)
        except Exception as e:
            logger.warning(f'Error getting name for {address}: {e!s}')
            name = 'Unknown'

        # Get symbol - handle both ByteArray and felt252 return types
        try:
            symbol_result = await contract.functions['symbol'].call()
            symbol = symbol_result[0]
            # If symbol is an integer (felt252), convert it to string
            if isinstance(symbol, int):
                symbol = felt_to_string(symbol)
        except Exception as e:
            logger.warning(f'Error getting symbol for {address}: {e!s}')
            symbol = 'UNK'

        # Get decimals
        try:
            decimals_result = await contract.functions['decimals'].call()
            decimals = decimals_result[0]
        except Exception as e:
            logger.warning(f'Error getting decimals for {address}: {e!s}')
            decimals = 18  # Default to 18 decimals if there's an error

        return name, symbol, decimals

    except Exception as e:
        logger.error(f'Error getting token info for {address}: {e!s}', exc_info=True)
        return 'Unknown', 'UNK', 18  # Default to 18 decimals if there's an error
