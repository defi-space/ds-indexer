from typing import TypedDict, List, Optional
import aiohttp
from decimal import Decimal

class TokenInfo(TypedDict):
    address: str
    name: str
    symbol: str

class PairInfo(TypedDict):
    chainId: str
    pairAddress: str
    baseToken: TokenInfo
    quoteToken: TokenInfo
    priceUsd: Optional[str]
    liquidity: dict
    volume: dict

async def get_token_pairs(chain_id: str, token_address: str) -> List[PairInfo]:
    """Fetch token pair data from DexScreener API."""
    url = f"https://api.dexscreener.com/token-pairs/v1/{chain_id}/{token_address}"
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status != 200:
                return []
            data = await response.json()
            return data 