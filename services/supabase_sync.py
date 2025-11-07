"""
Supabase Sync Service
Syncs Polymarket data to Supabase database
"""
import os
from datetime import datetime
from typing import Dict, List, Optional
from supabase import create_client, Client

class SupabaseSync:
    """Sync Polymarket data to Supabase"""

    def __init__(self):
        url: str = os.getenv("SUPABASE_URL")
        key: str = os.getenv("SUPABASE_KEY")
        self.client: Client = create_client(url, key)

    async def sync_market(self, market_data: Dict) -> Optional[str]:
        """
        Sync a single market to Supabase

        Args:
            market_data: Market data from Polymarket

        Returns:
            Market ID if successful
        """
        try:
            # Check if market already exists
            existing = self.client.table("markets")\
                .select("id")\
                .eq("id", market_data["id"])\
                .execute()

            market_row = {
                "id": market_data["id"],
                "title": market_data["title"],
                "description": market_data.get("description", ""),
                "category": market_data.get("category", "Other"),
                "odds_yes": market_data["odds_yes"],
                "odds_no": market_data["odds_no"],
                "volume": market_data.get("volume", 0),
                "liquidity": market_data.get("liquidity", 0),
                "deadline": market_data.get("end_date", datetime.utcnow().isoformat()),
                "status": market_data.get("status", "active"),
                "updated_at": datetime.utcnow().isoformat()
            }

            if existing.data:
                # Update existing market
                self.client.table("markets")\
                    .update(market_row)\
                    .eq("id", market_data["id"])\
                    .execute()
            else:
                # Insert new market
                market_row["created_at"] = datetime.utcnow().isoformat()
                self.client.table("markets")\
                    .insert(market_row)\
                    .execute()

            return market_data["id"]

        except Exception as e:
            print(f"Error syncing market: {e}")
            return None

    async def sync_markets_batch(self, markets: List[Dict]) -> int:
        """
        Sync multiple markets

        Args:
            markets: List of market data

        Returns:
            Number of markets synced
        """
        synced = 0
        for market in markets:
            result = await self.sync_market(market)
            if result:
                synced += 1

        return synced

    async def save_ai_analysis(
        self,
        market_id: str,
        analysis: Dict
    ) -> Optional[str]:
        """
        Save AI analysis to Supabase

        Args:
            market_id: Market ID
            analysis: Analysis data from Claude

        Returns:
            Analysis ID if successful
        """
        try:
            # Check if analysis exists
            existing = self.client.table("ai_analysis")\
                .select("id")\
                .eq("market_id", market_id)\
                .order("analyzed_at", desc=True)\
                .limit(1)\
                .execute()

            analysis_row = {
                "market_id": market_id,
                "confidence": analysis["confidence"],
                "reasoning": "\n".join(analysis["reasoning"]),
                "sentiment": analysis["sentiment"],
                "risk_level": analysis["risk_level"],
                "sources": analysis.get("key_factors", []),
                "analyzed_at": datetime.utcnow().isoformat()
            }

            # Always insert new analysis (keep history)
            result = self.client.table("ai_analysis")\
                .insert(analysis_row)\
                .execute()

            return result.data[0]["id"] if result.data else None

        except Exception as e:
            print(f"Error saving AI analysis: {e}")
            return None

    async def get_market(self, market_id: str) -> Optional[Dict]:
        """Get market from Supabase"""
        try:
            result = self.client.table("markets")\
                .select("*")\
                .eq("id", market_id)\
                .single()\
                .execute()

            return result.data if result.data else None

        except Exception as e:
            print(f"Error getting market: {e}")
            return None

    async def get_markets(
        self,
        limit: int = 20,
        offset: int = 0,
        status: str = "active"
    ) -> List[Dict]:
        """Get markets from Supabase"""
        try:
            query = self.client.table("markets")\
                .select("*")\
                .eq("status", status)\
                .order("volume", desc=True)\
                .limit(limit)\
                .offset(offset)

            result = query.execute()
            return result.data if result.data else []

        except Exception as e:
            print(f"Error getting markets: {e}")
            return []

    async def get_latest_analysis(self, market_id: str) -> Optional[Dict]:
        """Get latest AI analysis for a market"""
        try:
            result = self.client.table("ai_analysis")\
                .select("*")\
                .eq("market_id", market_id)\
                .order("analyzed_at", desc=True)\
                .limit(1)\
                .execute()

            return result.data[0] if result.data else None

        except Exception as e:
            print(f"Error getting analysis: {e}")
            return None

    async def save_prediction(
        self,
        market_id: str,
        user_address: str,
        outcome: str,
        amount: float
    ) -> Optional[str]:
        """Save user prediction"""
        try:
            prediction_row = {
                "market_id": market_id,
                "user_address": user_address,
                "outcome": outcome,
                "amount": amount,
                "timestamp": datetime.utcnow().isoformat()
            }

            result = self.client.table("predictions")\
                .insert(prediction_row)\
                .execute()

            # Update user portfolio
            await self._update_portfolio(user_address, amount)

            return result.data[0]["id"] if result.data else None

        except Exception as e:
            print(f"Error saving prediction: {e}")
            return None

    async def _update_portfolio(self, user_address: str, amount: float):
        """Update user portfolio stats"""
        try:
            # Check if portfolio exists
            existing = self.client.table("user_portfolios")\
                .select("*")\
                .eq("user_address", user_address)\
                .execute()

            if existing.data:
                # Update existing
                portfolio = existing.data[0]
                self.client.table("user_portfolios")\
                    .update({
                        "total_value": portfolio["total_value"] + amount,
                        "open_positions": portfolio["open_positions"] + 1,
                        "updated_at": datetime.utcnow().isoformat()
                    })\
                    .eq("user_address", user_address)\
                    .execute()
            else:
                # Create new
                self.client.table("user_portfolios")\
                    .insert({
                        "user_address": user_address,
                        "total_value": amount,
                        "open_positions": 1,
                        "win_rate": 0.0,
                        "created_at": datetime.utcnow().isoformat()
                    })\
                    .execute()

        except Exception as e:
            print(f"Error updating portfolio: {e}")


# Initialize singleton
supabase_sync = SupabaseSync()
