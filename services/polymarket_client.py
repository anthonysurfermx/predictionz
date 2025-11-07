"""
Polymarket API Client
Fetches market data from Polymarket CLOB
"""
import httpx
import json
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
                # Use closed=false and active=true to get only open/active markets
                response = await client.get(
                    f"{self.gamma_api_url}/markets",
                    params={
                        "limit": limit,
                        "offset": offset,
                        "closed": "false",  # Only non-closed markets
                        "active": "true"     # Only active markets
                    }
                )
                response.raise_for_status()
                data = response.json()

                # Simplify market data
                markets = []
                for market in data:
                    # Skip markets without slug (needed for URL) or that are closed
                    if not market.get("slug") or market.get("closed"):
                        continue

                    # Skip markets without conditionId
                    if not market.get("conditionId"):
                        continue

                    # Skip expired markets (end_date in the past)
                    end_date_str = market.get("endDate")
                    if end_date_str:
                        try:
                            end_date = datetime.fromisoformat(end_date_str.replace('Z', '+00:00'))
                            now = datetime.now(end_date.tzinfo) if end_date.tzinfo else datetime.now()
                            if end_date < now:
                                # Market has expired
                                continue
                        except:
                            # If date parsing fails, skip to be safe
                            pass

                    # Parse outcome prices (they're JSON strings)
                    outcome_prices = market.get("outcomePrices", "[\"0.5\", \"0.5\"]")
                    if isinstance(outcome_prices, str):
                        outcome_prices = json.loads(outcome_prices)

                    markets.append({
                        "id": market.get("conditionId"),
                        "slug": market.get("slug"),
                        "title": market.get("question"),
                        "description": market.get("description", ""),
                        "category": market.get("category", "Other"),
                        "odds_yes": float(outcome_prices[0]) if len(outcome_prices) > 0 else 0.5,
                        "odds_no": float(outcome_prices[1]) if len(outcome_prices) > 1 else 0.5,
                        "volume": float(market.get("volume", 0)),
                        "liquidity": float(market.get("liquidity", 0)),
                        "end_date": market.get("endDate"),
                        "image": market.get("image"),
                        "tokens": json.loads(market.get("clobTokenIds", "[]")) if isinstance(market.get("clobTokenIds"), str) else market.get("clobTokenIds", []),
                        "status": "active" if market.get("active") and not market.get("closed") else "closed"
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
                # Use condition_ids parameter to get specific market directly
                response = await client.get(
                    f"{self.gamma_api_url}/markets",
                    params={
                        "condition_ids": condition_id,
                        "closed": "false"  # Only get if not closed
                    }
                )
                response.raise_for_status()
                markets = response.json()

                # Should return single market or empty array
                if not markets or len(markets) == 0:
                    return None

                market = markets[0]

                # Double-check it has required fields
                if not market.get("slug"):
                    return None

                # Parse outcome prices (they're JSON strings)
                outcome_prices = market.get("outcomePrices", "[\"0.5\", \"0.5\"]")
                if isinstance(outcome_prices, str):
                    outcome_prices = json.loads(outcome_prices)

                return {
                    "id": market.get("conditionId"),
                    "slug": market.get("slug"),
                    "title": market.get("question"),
                    "description": market.get("description", ""),
                    "category": market.get("category", "Other"),
                    "odds_yes": float(outcome_prices[0]) if len(outcome_prices) > 0 else 0.5,
                    "odds_no": float(outcome_prices[1]) if len(outcome_prices) > 1 else 0.5,
                    "volume": float(market.get("volume", 0)),
                    "liquidity": float(market.get("liquidity", 0)),
                    "end_date": market.get("endDate"),
                    "image": market.get("image"),
                    "tokens": json.loads(market.get("clobTokenIds", "[]")) if isinstance(market.get("clobTokenIds"), str) else market.get("clobTokenIds", []),
                    "rewards": market.get("rewards", {}),
                    "created_at": market.get("createdAt"),
                    "status": "active" if market.get("active") and not market.get("closed") else "closed"
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
