"""
PredictionZ Recommendation Engine
Gen Z-focused personalized market discovery system
"""
from typing import List, Dict, Optional
from datetime import datetime
import re


class RecommendationEngine:
    """
    Intelligent recommendation system that matches markets to user preferences
    using category matching, risk tolerance, sentiment analysis, and trend signals.
    """

    # Category mappings (Polymarket categories to Gen Z-friendly labels)
    CATEGORY_MAPPING = {
        # Politics
        "US-current-affairs": ["politics", "news", "usa", "government"],
        "Politics": ["politics", "elections", "government"],

        # Crypto & Tech
        "Crypto": ["crypto", "web3", "blockchain", "defi"],
        "Tech": ["tech", "ai", "startup", "innovation"],

        # Sports
        "Sports": ["sports", "football", "basketball", "soccer"],

        # Entertainment & Culture
        "Pop Culture": ["culture", "entertainment", "music", "movies"],
        "Entertainment": ["culture", "entertainment", "celebrity"],

        # Finance
        "Finance": ["finance", "stocks", "economy", "business"],

        # Other
        "Science": ["science", "health", "research"],
        "Other": ["misc", "other"]
    }

    # Gen Z interest categories
    GEN_Z_CATEGORIES = {
        "politics": ["election", "trump", "biden", "congress", "president", "vote", "democracy"],
        "crypto": ["bitcoin", "ethereum", "nft", "defi", "web3", "crypto", "blockchain"],
        "tech": ["ai", "startup", "tesla", "apple", "meta", "google", "tech"],
        "sports": ["nfl", "nba", "fifa", "soccer", "football", "basketball", "sports"],
        "culture": ["music", "movie", "celebrity", "tiktok", "instagram", "viral"],
        "finance": ["stock", "market", "economy", "recession", "inflation", "fed"],
        "degen": ["meme", "yolo", "moon", "pump", "ape", "degen"]
    }

    # Risk level keywords
    RISK_KEYWORDS = {
        "safe": ["established", "likely", "probable", "consensus", "obvious"],
        "medium": ["possible", "potential", "could", "might", "uncertain"],
        "degen": ["unlikely", "moon", "longshot", "upset", "underdog", "wild"]
    }

    def __init__(self):
        """Initialize the recommendation engine"""
        pass

    def score_market(
        self,
        market: Dict,
        user_preferences: Dict,
        analysis: Optional[Dict] = None
    ) -> float:
        """
        Calculate a recommendation score (0-100) for a market based on user preferences.

        Args:
            market: Market data from Polymarket
            user_preferences: User's interests and settings
                {
                    "categories": ["crypto", "tech"],
                    "risk_tolerance": "medium",  # "safe", "medium", "degen"
                    "min_confidence": 0.6,
                    "min_volume": 10000,
                    "sentiment_preference": "bullish"  # "bullish", "bearish", "neutral"
                }
            analysis: Optional AI analysis data

        Returns:
            float: Score from 0-100
        """
        score = 0.0
        max_score = 100.0

        # 1. Category Match (40 points max)
        category_score = self._score_category_match(market, user_preferences)
        score += category_score * 0.4

        # 2. Risk Match (20 points max)
        risk_score = self._score_risk_match(market, user_preferences, analysis)
        score += risk_score * 0.2

        # 3. Volume/Liquidity (15 points max)
        volume_score = self._score_volume(market, user_preferences)
        score += volume_score * 0.15

        # 4. AI Confidence (15 points max)
        if analysis:
            confidence_score = self._score_confidence(analysis, user_preferences)
            score += confidence_score * 0.15

        # 5. Sentiment Match (10 points max)
        if analysis:
            sentiment_score = self._score_sentiment(analysis, user_preferences)
            score += sentiment_score * 0.1

        return min(score, max_score)

    def _score_category_match(self, market: Dict, preferences: Dict) -> float:
        """
        Score based on category match (0-100)
        """
        user_categories = preferences.get("categories", [])
        if not user_categories:
            return 50.0  # Neutral if no preferences

        market_category = market.get("category", "").lower()
        market_title = market.get("title", "").lower()
        market_description = market.get("description", "").lower()

        text_to_search = f"{market_category} {market_title} {market_description}"

        match_score = 0.0
        matches = 0

        for user_cat in user_categories:
            user_cat_lower = user_cat.lower()

            # Check if user category keywords appear in market
            if user_cat_lower in self.GEN_Z_CATEGORIES:
                keywords = self.GEN_Z_CATEGORIES[user_cat_lower]
                for keyword in keywords:
                    if keyword in text_to_search:
                        matches += 1
                        break

            # Direct category match
            for poly_cat, tags in self.CATEGORY_MAPPING.items():
                if user_cat_lower in tags and poly_cat.lower() in market_category:
                    matches += 1
                    break

        if matches > 0:
            match_score = min(100.0, (matches / len(user_categories)) * 100)

        return match_score

    def _score_risk_match(
        self,
        market: Dict,
        preferences: Dict,
        analysis: Optional[Dict]
    ) -> float:
        """
        Score based on risk tolerance match (0-100)
        """
        user_risk = preferences.get("risk_tolerance", "medium").lower()

        # Get risk from AI analysis if available
        if analysis and "risk_level" in analysis:
            market_risk = analysis["risk_level"]  # 1-5 scale

            # Map risk level to categories
            if market_risk <= 2:
                market_risk_cat = "safe"
            elif market_risk <= 3:
                market_risk_cat = "medium"
            else:
                market_risk_cat = "degen"

            # Perfect match = 100, adjacent = 60, opposite = 20
            if user_risk == market_risk_cat:
                return 100.0
            elif (user_risk == "medium") or (market_risk_cat == "medium"):
                return 60.0
            else:
                return 20.0

        # Fallback: analyze odds spread
        odds_yes = market.get("odds_yes", 0.5)
        odds_no = market.get("odds_no", 0.5)

        # Closer odds = higher risk
        odds_spread = abs(odds_yes - odds_no)

        if odds_spread > 0.6:  # 80/20 or more
            market_risk_cat = "safe"
        elif odds_spread > 0.3:  # 65/35 to 80/20
            market_risk_cat = "medium"
        else:  # < 65/35
            market_risk_cat = "degen"

        if user_risk == market_risk_cat:
            return 100.0
        elif (user_risk == "medium") or (market_risk_cat == "medium"):
            return 60.0
        else:
            return 20.0

    def _score_volume(self, market: Dict, preferences: Dict) -> float:
        """
        Score based on volume/liquidity (0-100)
        Higher volume = more liquid = better (usually)
        """
        volume = market.get("volume", 0)
        min_volume = preferences.get("min_volume", 0)

        # Must meet minimum
        if volume < min_volume:
            return 0.0

        # Score based on volume tiers
        if volume >= 1_000_000:  # $1M+
            return 100.0
        elif volume >= 500_000:  # $500K+
            return 85.0
        elif volume >= 100_000:  # $100K+
            return 70.0
        elif volume >= 50_000:  # $50K+
            return 55.0
        elif volume >= 10_000:  # $10K+
            return 40.0
        else:
            return 25.0

    def _score_confidence(self, analysis: Dict, preferences: Dict) -> float:
        """
        Score based on AI confidence level (0-100)
        """
        confidence = analysis.get("confidence", 0.5)
        min_confidence = preferences.get("min_confidence", 0.0)

        # Must meet minimum
        if confidence < min_confidence:
            return 0.0

        # Higher confidence = better (scale 0-1 to 0-100)
        return confidence * 100

    def _score_sentiment(self, analysis: Dict, preferences: Dict) -> float:
        """
        Score based on sentiment match (0-100)
        """
        sentiment_pref = preferences.get("sentiment_preference", None)
        if not sentiment_pref:
            return 50.0  # Neutral if no preference

        market_sentiment = analysis.get("sentiment", "neutral").lower()

        if sentiment_pref.lower() == market_sentiment:
            return 100.0
        elif market_sentiment == "neutral":
            return 60.0
        else:
            return 30.0

    def rank_markets(
        self,
        markets: List[Dict],
        user_preferences: Dict,
        analyses: Optional[Dict[str, Dict]] = None
    ) -> List[Dict]:
        """
        Rank a list of markets by recommendation score.

        Args:
            markets: List of market dicts
            user_preferences: User's preferences
            analyses: Optional dict mapping market_id -> analysis

        Returns:
            List of markets with added "recommendation_score" field, sorted by score
        """
        scored_markets = []

        for market in markets:
            market_id = market.get("id")
            analysis = None

            if analyses and market_id in analyses:
                analysis = analyses[market_id]

            score = self.score_market(market, user_preferences, analysis)

            # Add score to market dict
            market_with_score = market.copy()
            market_with_score["recommendation_score"] = round(score, 2)

            scored_markets.append(market_with_score)

        # Sort by score (highest first)
        scored_markets.sort(key=lambda m: m["recommendation_score"], reverse=True)

        return scored_markets

    def get_trending_markets(self, markets: List[Dict], limit: int = 10) -> List[Dict]:
        """
        Get trending markets based on volume, activity, and recency.

        Args:
            markets: List of markets
            limit: Max number to return

        Returns:
            List of trending markets
        """
        # Score by volume + liquidity
        scored = []

        for market in markets:
            volume = market.get("volume", 0)
            liquidity = market.get("liquidity", 0)

            # Trending score = volume + (liquidity * 0.5)
            trend_score = volume + (liquidity * 0.5)

            scored.append({
                **market,
                "trend_score": trend_score
            })

        # Sort by trend score
        scored.sort(key=lambda m: m["trend_score"], reverse=True)

        return scored[:limit]

    def detect_category(self, text: str) -> List[str]:
        """
        Detect categories from text (for auto-tagging).

        Args:
            text: Market title or description

        Returns:
            List of detected category tags
        """
        text_lower = text.lower()
        detected = []

        for category, keywords in self.GEN_Z_CATEGORIES.items():
            for keyword in keywords:
                if keyword in text_lower:
                    detected.append(category)
                    break

        return list(set(detected))  # Remove duplicates

    def get_similar_markets(
        self,
        market: Dict,
        all_markets: List[Dict],
        limit: int = 5
    ) -> List[Dict]:
        """
        Find similar markets based on category and keywords.

        Args:
            market: Reference market
            all_markets: All available markets
            limit: Max number to return

        Returns:
            List of similar markets
        """
        market_id = market.get("id")
        market_category = market.get("category", "").lower()
        market_text = f"{market.get('title', '')} {market.get('description', '')}".lower()

        # Detect keywords
        market_tags = self.detect_category(market_text)

        similar = []

        for other in all_markets:
            # Skip same market
            if other.get("id") == market_id:
                continue

            other_category = other.get("category", "").lower()
            other_text = f"{other.get('title', '')} {other.get('description', '')}".lower()
            other_tags = self.detect_category(other_text)

            similarity = 0.0

            # Category match (50 points)
            if market_category == other_category:
                similarity += 50.0

            # Tag overlap (50 points)
            if market_tags and other_tags:
                overlap = len(set(market_tags) & set(other_tags))
                tag_score = (overlap / len(market_tags)) * 50
                similarity += tag_score

            if similarity > 0:
                similar.append({
                    **other,
                    "similarity_score": similarity
                })

        # Sort by similarity
        similar.sort(key=lambda m: m["similarity_score"], reverse=True)

        return similar[:limit]


# Global instance
recommendation_engine = RecommendationEngine()
