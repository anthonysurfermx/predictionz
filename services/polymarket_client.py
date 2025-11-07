"""
Polymarket API Client
Fetches market data from Polymarket CLOB
"""
import httpx
from typing import Dict, List, Optional
from datetime import datetime

class PolymarketClient:
    """Client for Polymarket CLOB API"""

    def __init__(self, api_url: str = "https://clob.polymarket.com"):
        self.api_url = api_url
        self.gamma_api_url = "https://gamma-api.polymarket.com"

    async def get_markets(
        self,
        limit: int = 20,
        offset: int = 0,
        active: bool = True
    ) -> List[Dict]:
        """
        Get list of markets from Gamma API

        Returns:
            List of market objects with simplified structure
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Gamma Markets API provides market metadata
                response = await client.get(
                    f"{self.gamma_api_url}/markets",
                    params={
                        "limit": limit,
                        "offset": offset,
                        "active": str(active).lower()
                    }
                )
                response.raise_for_status()
                data = response.json()

                # Simplify market data
                markets = []
                for market in data:
                    markets.append({
                        "id": market.get("condition_id"),
                        "slug": market.get("slug"),
                        "title": market.get("question"),
                        "description": market.get("description", ""),
                        "category": market.get("category", "Other"),
                        "odds_yes": float(market.get("outcomePrices", ["0.5", "0.5"])[0]),
                        "odds_no": float(market.get("outcomePrices", ["0.5", "0.5"])[1]),
                        "volume": float(market.get("volume", 0)),
                        "liquidity": float(market.get("liquidity", 0)),
                        "end_date": market.get("endDate"),
                        "image": market.get("image"),
                        "tokens": market.get("tokens", []),
                        "status": "active" if market.get("active") else "closed"
                    })

                return markets

        except Exception as e:
            print(f"Error fetching markets: {e}")
            return []

    async def get_market_detail(self, condition_id: str) -> Optional[Dict]:
        """
        Get detailed market information

        Args:
            condition_id: Market condition ID

        Returns:
            Detailed market object
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.gamma_api_url}/markets/{condition_id}"
                )
                response.raise_for_status()
                market = response.json()

                return {
                    "id": market.get("condition_id"),
                    "slug": market.get("slug"),
                    "title": market.get("question"),
                    "description": market.get("description", ""),
                    "category": market.get("category", "Other"),
                    "odds_yes": float(market.get("outcomePrices", ["0.5", "0.5"])[0]),
                    "odds_no": float(market.get("outcomePrices", ["0.5", "0.5"])[1]),
                    "volume": float(market.get("volume", 0)),
                    "liquidity": float(market.get("liquidity", 0)),
                    "end_date": market.get("endDate"),
                    "image": market.get("image"),
                    "tokens": market.get("tokens", []),
                    "rewards": market.get("rewards", {}),
                    "created_at": market.get("createdAt"),
                    "status": "active" if market.get("active") else "closed"
                }

        except Exception as e:
            print(f"Error fetching market detail: {e}")
            return None

    async def get_orderbook(self, token_id: str) -> Dict:
        """
        Get orderbook for a specific token

        Args:
            token_id: Token ID for YES or NO outcome

        Returns:
            Orderbook with bids and asks
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.api_url}/book",
                    params={"token_id": token_id}
                )
                response.raise_for_status()
                return response.json()

        except Exception as e:
            print(f"Error fetching orderbook: {e}")
            return {"bids": [], "asks": []}

    async def get_market_trades(
        self,
        condition_id: str,
        limit: int = 50
    ) -> List[Dict]:
        """
        Get recent trades for a market

        Args:
            condition_id: Market condition ID
            limit: Number of trades to fetch

        Returns:
            List of recent trades
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.gamma_api_url}/markets/{condition_id}/trades",
                    params={"limit": limit}
                )
                response.raise_for_status()
                return response.json()

        except Exception as e:
            print(f"Error fetching trades: {e}")
            return []

    async def search_markets(self, query: str) -> List[Dict]:
        """
        Search markets by keyword

        Args:
            query: Search query

        Returns:
            List of matching markets
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.gamma_api_url}/markets",
                    params={"query": query}
                )
                response.raise_for_status()
                data = response.json()

                markets = []
                for market in data:
                    markets.append({
                        "id": market.get("condition_id"),
                        "title": market.get("question"),
                        "odds_yes": float(market.get("outcomePrices", ["0.5", "0.5"])[0]),
                        "odds_no": float(market.get("outcomePrices", ["0.5", "0.5"])[1]),
                        "volume": float(market.get("volume", 0)),
                    })

                return markets

        except Exception as e:
            print(f"Error searching markets: {e}")
            return []


# Initialize singleton
polymarket_client = PolymarketClient()
