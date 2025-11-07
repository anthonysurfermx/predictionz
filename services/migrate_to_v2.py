"""
Migration helper to transition from recommendation_engine to V2
This script helps you test and migrate gradually
"""
from typing import Dict, List, Optional
from services.recommendation_engine import recommendation_engine as engine_v1
from services.recommendation_engine_v2 import (
    recommendation_engine_v2 as engine_v2,
    UserProfile,
    Weights
)


class RecommendationEngineAdapter:
    """
    Adapter that can use V1 or V2 engine.
    Allows gradual migration and A/B testing.
    """

    def __init__(self, use_v2: bool = False, custom_weights: Optional[Weights] = None):
        """
        Args:
            use_v2: If True, use V2 engine; if False, use V1
            custom_weights: Optional custom weights for V2
        """
        self.use_v2 = use_v2
        self.engine_v1 = engine_v1
        self.engine_v2 = engine_v2 if not custom_weights else engine_v2.__class__(custom_weights)

    def score_market(
        self,
        market: Dict,
        user_preferences: Dict,
        analysis: Optional[Dict] = None,
        **v2_kwargs
    ):
        """
        Score a market using either V1 or V2 engine.

        Args (V1 compatible):
            market: Market data
            user_preferences: User preferences dict
            analysis: Optional AI analysis

        Additional args for V2:
            user_profile: UserProfile object
            context_tokens: Viral context dict

        Returns:
            V1: float score
            V2: (score, breakdown) tuple
        """
        if self.use_v2:
            score, breakdown = self.engine_v2.score_market(
                market,
                user_preferences,
                analysis,
                user_profile=v2_kwargs.get("user_profile"),
                context_tokens=v2_kwargs.get("context_tokens")
            )
            # For compatibility, can return just score or tuple
            if v2_kwargs.get("return_breakdown", False):
                return score, breakdown
            return score
        else:
            return self.engine_v1.score_market(market, user_preferences, analysis)

    def rank_markets(
        self,
        markets: List[Dict],
        user_preferences: Dict,
        analyses: Optional[Dict[str, Dict]] = None,
        **v2_kwargs
    ) -> List[Dict]:
        """
        Rank markets using either V1 or V2 engine.

        Additional V2 args:
            user_profile: UserProfile
            context_tokens: Viral context
            k: Number of results
            diversity_lambda: MMR diversity (0-1)
        """
        if self.use_v2:
            return self.engine_v2.rank_markets(
                markets,
                user_preferences,
                analyses,
                user_profile=v2_kwargs.get("user_profile"),
                context_tokens=v2_kwargs.get("context_tokens"),
                k=v2_kwargs.get("k", 50),
                diversity_lambda=v2_kwargs.get("diversity_lambda", 0.7)
            )
        else:
            return self.engine_v1.rank_markets(markets, user_preferences, analyses)

    def get_trending_markets(
        self,
        markets: List[Dict],
        limit: int = 10,
        **v2_kwargs
    ) -> List[Dict]:
        """Get trending markets"""
        if self.use_v2:
            return self.engine_v2.get_trending_markets(
                markets,
                limit,
                context_tokens=v2_kwargs.get("context_tokens")
            )
        else:
            return self.engine_v1.get_trending_markets(markets, limit)

    def detect_category(self, text: str) -> List[str]:
        """Detect categories (both engines have this)"""
        if self.use_v2:
            return self.engine_v2.detect_category(text)
        else:
            return self.engine_v1.detect_category(text)


# Example: Creating UserProfile from Instagram analysis
def create_profile_from_instagram(
    username: str,
    instagram_analysis: Dict,
    user_id: Optional[str] = None
) -> UserProfile:
    """
    Convert Instagram analysis to UserProfile for V2 engine.

    Args:
        username: Instagram username
        instagram_analysis: Result from instagram_analyzer
        user_id: Optional user ID

    Returns:
        UserProfile object
    """
    interests = instagram_analysis.get("interests", {})

    return UserProfile(
        user_id=user_id or username,
        categories=interests.get("categories", []),
        risk_tolerance=interests.get("risk_tolerance", "medium"),
        interest_embedding=instagram_analysis.get("embedding"),  # If available
        time_horizon="balanced"  # Can be inferred from posts
    )


# Example: Creating UserProfile from manual quiz
def create_profile_from_quiz(
    user_preferences: Dict,
    user_id: str = "anonymous"
) -> UserProfile:
    """
    Convert manual quiz preferences to UserProfile.

    Args:
        user_preferences: From manual quiz
        user_id: User identifier

    Returns:
        UserProfile object
    """
    return UserProfile(
        user_id=user_id,
        categories=user_preferences.get("categories", []),
        risk_tolerance=user_preferences.get("risk_tolerance", "medium"),
        min_volume=user_preferences.get("min_volume", 0),
        min_confidence=user_preferences.get("min_confidence", 0.0),
        sentiment_preference=user_preferences.get("sentiment_preference"),
        interest_embedding=user_preferences.get("interest_embedding")
    )


# Example: A/B testing comparison
def compare_engines(
    market: Dict,
    user_preferences: Dict,
    analysis: Optional[Dict] = None
) -> Dict:
    """
    Compare V1 and V2 engine scores for debugging/testing.

    Returns:
        {
            "v1_score": float,
            "v2_score": float,
            "v2_breakdown": dict,
            "difference": float
        }
    """
    adapter_v1 = RecommendationEngineAdapter(use_v2=False)
    adapter_v2 = RecommendationEngineAdapter(use_v2=True)

    v1_score = adapter_v1.score_market(market, user_preferences, analysis)
    v2_score, v2_breakdown = adapter_v2.score_market(
        market, user_preferences, analysis, return_breakdown=True
    )

    return {
        "v1_score": round(v1_score, 2),
        "v2_score": round(v2_score, 2),
        "v2_breakdown": v2_breakdown,
        "difference": round(v2_score - v1_score, 2)
    }


# Global adapter instance (set to V1 by default for safety)
recommendation_adapter = RecommendationEngineAdapter(use_v2=False)


if __name__ == "__main__":
    """
    Test script to compare V1 vs V2 engines
    """
    print("🔬 Testing Recommendation Engine V1 vs V2\n")

    # Sample market
    test_market = {
        "id": "test-123",
        "title": "Will Bitcoin hit $100K in 2024?",
        "description": "Prediction market for Bitcoin reaching $100,000 by end of 2024",
        "category": "Crypto",
        "odds_yes": 0.65,
        "odds_no": 0.35,
        "volume": 250000,
        "liquidity": 150000,
        "volume_24h": 50000,
        "volume_7d": 200000,
        "traders_24h": 120
    }

    # Sample user preferences
    test_prefs = {
        "categories": ["crypto", "tech"],
        "risk_tolerance": "medium",
        "min_volume": 10000,
        "min_confidence": 0.5
    }

    # Sample analysis
    test_analysis = {
        "confidence": 0.72,
        "risk_level": 3,
        "sentiment": "bullish",
        "volatility": 0.35,
        "social_buzz": 0.8
    }

    # Compare engines
    comparison = compare_engines(test_market, test_prefs, test_analysis)

    print("📊 Comparison Results:")
    print(f"   V1 Score: {comparison['v1_score']}")
    print(f"   V2 Score: {comparison['v2_score']}")
    print(f"   Difference: {comparison['difference']}")
    print(f"\n📈 V2 Breakdown:")
    for component, score in comparison['v2_breakdown'].items():
        print(f"   {component}: {round(score, 2)}")

    print("\n✅ Migration script ready!")
    print("   To enable V2: set use_v2=True in RecommendationEngineAdapter")
