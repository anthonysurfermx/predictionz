"""
Viral Context Service
Detects trending topics and viral moments to boost relevant markets
"""
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import re


class ViralContextService:
    """
    Service to detect and track viral/trending topics for market boosting.

    In production, this would integrate with:
    - Twitter/X API for trending hashtags
    - Reddit API for r/all hot posts
    - Google Trends API
    - News APIs

    For now, uses manual configuration + basic keyword detection.
    """

    def __init__(self):
        """Initialize viral context tracking"""
        # Manual trending topics (update regularly or via API)
        self.trending_topics = self._get_current_trends()

        # Seasonal/recurring events
        self.seasonal_events = self._get_seasonal_events()

    def _get_current_trends(self) -> Dict[str, float]:
        """
        Get current trending topics with weight (0-1).

        In production: Fetch from Twitter/Reddit/Google Trends APIs
        For now: Manually configured

        Returns:
            {
                "topic_keyword": weight (0-1)
            }
        """
        # Example trending topics (update these regularly!)
        trends = {
            # Politics (always trending in election years)
            "election": 0.9,
            "trump": 0.8,
            "biden": 0.7,
            "2024": 0.6,

            # Crypto (usually trending)
            "bitcoin": 0.8,
            "btc": 0.8,
            "ethereum": 0.7,
            "crypto": 0.7,

            # Tech
            "ai": 0.9,
            "chatgpt": 0.8,
            "openai": 0.7,

            # Sports (update based on season)
            "superbowl": 0.0,  # Not season
            "nfl": 0.5,
            "nba": 0.6,
            "worldcup": 0.0,   # Not World Cup year

            # Culture
            "taylor": 0.7,  # Taylor Swift always trending
            "drake": 0.6,
            "netflix": 0.5,

            # Viral moments (update frequently!)
            # "grammys": 0.9,  # Would be 1.0 during Grammys week
            # "oscars": 0.0,   # Not Oscar season
        }

        return trends

    def _get_seasonal_events(self) -> List[Dict]:
        """
        Get seasonal/recurring events with date ranges.

        Returns:
            List of events with start/end dates and keywords
        """
        # Get current year
        year = datetime.now().year

        events = [
            # Sports
            {
                "name": "Super Bowl",
                "keywords": ["superbowl", "super bowl", "nfl championship"],
                "start": datetime(year, 2, 1),
                "end": datetime(year, 2, 15),
                "weight": 1.0
            },
            {
                "name": "March Madness",
                "keywords": ["march madness", "ncaa tournament", "college basketball"],
                "start": datetime(year, 3, 15),
                "end": datetime(year, 4, 10),
                "weight": 0.9
            },
            {
                "name": "NBA Playoffs",
                "keywords": ["nba playoffs", "nba finals"],
                "start": datetime(year, 4, 15),
                "end": datetime(year, 6, 30),
                "weight": 0.8
            },

            # Awards
            {
                "name": "Grammys",
                "keywords": ["grammys", "grammy awards"],
                "start": datetime(year, 1, 25),
                "end": datetime(year, 2, 10),
                "weight": 0.9
            },
            {
                "name": "Oscars",
                "keywords": ["oscars", "academy awards"],
                "start": datetime(year, 2, 20),
                "end": datetime(year, 3, 15),
                "weight": 0.9
            },

            # Elections (US)
            {
                "name": "Election Season",
                "keywords": ["election", "vote", "polls", "debate"],
                "start": datetime(year, 9, 1),
                "end": datetime(year, 11, 10),
                "weight": 1.0
            },

            # Crypto events
            {
                "name": "Bitcoin Halving",
                "keywords": ["halving", "bitcoin halving"],
                "start": datetime(year, 4, 1),
                "end": datetime(year, 5, 1),
                "weight": 0.9
            }
        ]

        return events

    def get_viral_context(self, current_date: Optional[datetime] = None) -> Dict[str, float]:
        """
        Get current viral context with weights.

        Args:
            current_date: Optional date (defaults to now)

        Returns:
            {
                "keyword": weight (0-1)
            }
        """
        if current_date is None:
            current_date = datetime.now()

        context = {}

        # Add base trending topics
        context.update(self.trending_topics)

        # Add seasonal events that are active now
        for event in self.seasonal_events:
            if event["start"] <= current_date <= event["end"]:
                # Event is happening now!
                for keyword in event["keywords"]:
                    context[keyword] = event["weight"]

        return context

    def detect_viral_keywords_in_market(
        self,
        market_title: str,
        market_description: str = "",
        context: Optional[Dict[str, float]] = None
    ) -> Dict[str, float]:
        """
        Detect which viral keywords appear in a market.

        Args:
            market_title: Market title
            market_description: Market description
            context: Optional custom context (defaults to current viral context)

        Returns:
            {
                "detected_keyword": weight
            }
        """
        if context is None:
            context = self.get_viral_context()

        text = f"{market_title} {market_description}".lower()
        detected = {}

        for keyword, weight in context.items():
            # Check if keyword appears in text
            if keyword.lower() in text:
                detected[keyword] = weight

        return detected

    def get_viral_boost_score(
        self,
        market_title: str,
        market_description: str = ""
    ) -> float:
        """
        Get a single viral boost score (0-1) for a market.

        Args:
            market_title: Market title
            market_description: Market description

        Returns:
            Score 0-1 (0 = not viral, 1 = extremely viral)
        """
        detected = self.detect_viral_keywords_in_market(
            market_title, market_description
        )

        if not detected:
            return 0.0

        # Return highest weight found
        return max(detected.values())

    def update_trending_topics(self, new_trends: Dict[str, float]):
        """
        Update trending topics manually.

        Args:
            new_trends: New trending topics dict
        """
        self.trending_topics.update(new_trends)

    def add_custom_event(
        self,
        name: str,
        keywords: List[str],
        start: datetime,
        end: datetime,
        weight: float = 0.9
    ):
        """
        Add a custom event to track.

        Args:
            name: Event name
            keywords: Keywords to match
            start: Start date
            end: End date
            weight: Importance weight (0-1)
        """
        self.seasonal_events.append({
            "name": name,
            "keywords": keywords,
            "start": start,
            "end": end,
            "weight": weight
        })


# Global instance
viral_context_service = ViralContextService()


# Helper functions for easy integration

def get_current_viral_context() -> Dict[str, float]:
    """Get current viral/trending context"""
    return viral_context_service.get_viral_context()


def get_market_viral_score(market: Dict) -> float:
    """
    Get viral score for a market.

    Args:
        market: Market dict with title and description

    Returns:
        Viral score 0-1
    """
    return viral_context_service.get_viral_boost_score(
        market.get("title", ""),
        market.get("description", "")
    )


def enhance_markets_with_viral_scores(markets: List[Dict]) -> List[Dict]:
    """
    Add viral_score field to all markets.

    Args:
        markets: List of market dicts

    Returns:
        Markets with added viral_score field
    """
    context = viral_context_service.get_viral_context()

    enhanced = []
    for market in markets:
        market_copy = market.copy()
        viral_score = viral_context_service.get_viral_boost_score(
            market.get("title", ""),
            market.get("description", "")
        )
        market_copy["viral_score"] = viral_score
        enhanced.append(market_copy)

    return enhanced


if __name__ == "__main__":
    """
    Test viral context service
    """
    print("🔥 Testing Viral Context Service\n")

    # Test 1: Get current viral context
    print("1. Current Viral Context:")
    context = viral_context_service.get_viral_context()
    for keyword, weight in sorted(context.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"   {keyword}: {weight}")

    # Test 2: Detect in market
    print("\n2. Detecting viral keywords in markets:")
    test_markets = [
        {
            "title": "Will Bitcoin hit $100K in 2024?",
            "description": "Crypto prediction market"
        },
        {
            "title": "Will Trump win the 2024 election?",
            "description": "Presidential election betting"
        },
        {
            "title": "Will Taylor Swift release new album?",
            "description": "Music and pop culture bet"
        },
        {
            "title": "Will random startup succeed?",
            "description": "Small business prediction"
        }
    ]

    for market in test_markets:
        score = viral_context_service.get_viral_boost_score(
            market["title"], market["description"]
        )
        detected = viral_context_service.detect_viral_keywords_in_market(
            market["title"], market["description"]
        )

        print(f"\n   Market: {market['title']}")
        print(f"   Viral Score: {score:.2f}")
        if detected:
            print(f"   Detected: {list(detected.keys())}")

    # Test 3: Seasonal events
    print("\n3. Active Seasonal Events:")
    current = datetime.now()
    active_events = [
        event for event in viral_context_service.seasonal_events
        if event["start"] <= current <= event["end"]
    ]

    if active_events:
        for event in active_events:
            print(f"   🎉 {event['name']} (weight: {event['weight']})")
    else:
        print("   No active seasonal events right now")

    print("\n✅ Viral context service ready!")
