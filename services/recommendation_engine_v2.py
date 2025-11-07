"""
PredictionZ Recommendation Engine V2
Gen Z-focused personalized market discovery with semantic matching,
viral detection, and TikTok-style "For You" algorithm
"""
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timezone
import math
import re
from dataclasses import dataclass, field
from collections import defaultdict


@dataclass
class UserHistoryEvent:
    """Track user interaction with markets"""
    market_id: str
    action: str  # "view", "click", "bet"
    category: str
    risk_level: str  # "safe", "medium", "degen"
    timestamp: float
    engagement_score: float = 1.0  # Higher = more engaged


@dataclass
class UserProfile:
    """Enhanced user profile with learning capabilities"""
    user_id: str
    categories: List[str] = field(default_factory=list)
    risk_tolerance: str = "medium"

    # Learning weights (updated based on interactions)
    category_weights: Dict[str, float] = field(default_factory=dict)
    risk_adjustment: float = 0.0  # -1.0 (more safe) to +1.0 (more degen)

    # Engagement history
    history: List[UserHistoryEvent] = field(default_factory=list)

    # Embeddings (optional - for semantic matching)
    interest_embedding: Optional[List[float]] = None

    # Preferences
    min_volume: int = 0
    min_confidence: float = 0.0
    sentiment_preference: Optional[str] = None
    time_horizon: str = "balanced"  # "short", "long", "balanced"

    def learn_from_interaction(self, event: UserHistoryEvent):
        """Update profile based on user interaction"""
        self.history.append(event)

        # Boost category weight
        if event.category:
            current = self.category_weights.get(event.category, 1.0)
            self.category_weights[event.category] = min(2.0, current + 0.1 * event.engagement_score)

        # Adjust risk tolerance based on interactions
        risk_map = {"safe": -0.5, "medium": 0.0, "degen": 0.5}
        if event.risk_level in risk_map:
            adjustment = risk_map[event.risk_level] * 0.05 * event.engagement_score
            self.risk_adjustment = max(-1.0, min(1.0, self.risk_adjustment + adjustment))

    def get_effective_risk_tolerance(self) -> str:
        """Get current risk tolerance after adjustments"""
        base_map = {"safe": -0.5, "medium": 0.0, "degen": 0.5}
        base_value = base_map.get(self.risk_tolerance, 0.0)
        adjusted = base_value + self.risk_adjustment

        if adjusted < -0.25:
            return "safe"
        elif adjusted > 0.25:
            return "degen"
        else:
            return "medium"


@dataclass
class Weights:
    """Configurable scoring weights (must sum to ~1.0)"""
    semantic: float = 0.30  # Semantic/embedding similarity
    category: float = 0.20  # Category keyword match
    risk: float = 0.15      # Risk tolerance alignment
    trend: float = 0.15     # Trending/viral signals
    volume: float = 0.10    # Volume/liquidity
    confidence: float = 0.05  # AI confidence
    sentiment: float = 0.05   # Sentiment match

    def normalize(self):
        """Ensure weights sum to 1.0"""
        total = (self.semantic + self.category + self.risk + self.trend +
                self.volume + self.confidence + self.sentiment)
        if total > 0:
            self.semantic /= total
            self.category /= total
            self.risk /= total
            self.trend /= total
            self.volume /= total
            self.confidence /= total
            self.sentiment /= total


class RecommendationEngineV2:
    """
    Advanced recommendation system with:
    - Semantic understanding (embeddings)
    - Viral/trending detection
    - User profile learning
    - Diversity (MMR)
    - Gen Z cultural context
    """

    # Category mappings
    CATEGORY_MAPPING = {
        "US-current-affairs": ["politics", "news", "usa", "government"],
        "Politics": ["politics", "elections", "government"],
        "Crypto": ["crypto", "web3", "blockchain", "defi"],
        "Tech": ["tech", "ai", "startup", "innovation"],
        "Sports": ["sports", "football", "basketball", "soccer"],
        "Pop Culture": ["culture", "entertainment", "music", "movies"],
        "Entertainment": ["culture", "entertainment", "celebrity"],
        "Finance": ["finance", "stocks", "economy", "business"],
        "Science": ["science", "health", "research"],
        "Other": ["misc", "other"]
    }

    # Gen Z interest categories with expanded keywords
    GEN_Z_CATEGORIES = {
        "politics": [
            "election", "trump", "biden", "congress", "president", "vote", "democracy",
            "senate", "polls", "debate", "campaign", "governor", "mayor", "republican", "democrat"
        ],
        "crypto": [
            "bitcoin", "ethereum", "nft", "defi", "web3", "crypto", "blockchain",
            "btc", "eth", "solana", "binance", "coinbase", "wallet", "dex", "dao",
            "token", "coin", "mining", "hodl", "moon", "lambo"
        ],
        "tech": [
            "ai", "startup", "tesla", "apple", "meta", "google", "tech", "openai",
            "chatgpt", "robot", "drone", "space", "spacex", "elon", "innovation",
            "software", "app", "platform", "gadget", "iphone", "android"
        ],
        "sports": [
            "nfl", "nba", "fifa", "soccer", "football", "basketball", "sports",
            "championship", "playoffs", "superbowl", "worldcup", "olympics",
            "lebron", "curry", "mahomes", "messi", "ronaldo", "athlete"
        ],
        "culture": [
            "music", "movie", "celebrity", "tiktok", "instagram", "viral", "meme",
            "taylor", "drake", "beyonce", "kardashian", "netflix", "spotify",
            "concert", "festival", "grammy", "oscar", "emmy", "influencer",
            "cancelled", "ratio", "trending"
        ],
        "finance": [
            "stock", "market", "economy", "recession", "inflation", "fed", "wall street",
            "nasdaq", "dow", "s&p", "bull", "bear", "invest", "portfolio",
            "nvidia", "microsoft", "amazon", "tesla stock"
        ],
        "degen": [
            "meme", "yolo", "moon", "pump", "ape", "degen", "longshot",
            "underdog", "upset", "wildcard", "gamble", "bet", "risky"
        ]
    }

    # Gen Z slang and cultural context
    GEN_Z_SLANG = {
        "ratio": ["twitter drama", "cancelled", "viral controversy"],
        "no cap": ["truth", "honest", "real"],
        "fr": ["for real", "seriously"],
        "bussin": ["amazing", "great", "fire"],
        "mid": ["mediocre", "average", "meh"],
        "goat": ["greatest", "best", "legend"],
        "slay": ["dominate", "succeed", "win"],
        "stan": ["fan", "supporter", "follower"],
        "vibe": ["feeling", "mood", "energy"],
        "based": ["confident", "bold", "controversial"]
    }

    def __init__(self, weights: Optional[Weights] = None):
        """Initialize with configurable weights"""
        self.weights = weights or Weights()
        self.weights.normalize()

    def score_market(
        self,
        market: Dict,
        user_preferences: Dict,
        analysis: Optional[Dict] = None,
        user_profile: Optional[UserProfile] = None,
        context_tokens: Optional[Dict[str, float]] = None
    ) -> Tuple[float, Dict[str, float]]:
        """
        Calculate recommendation score with breakdown.

        Args:
            market: Market data
            user_preferences: Legacy preferences dict
            analysis: Optional AI analysis with embedding, confidence, etc.
            user_profile: Optional UserProfile for personalization
            context_tokens: Optional viral context {"worldcup": 1.0, "grammys": 0.8}

        Returns:
            (total_score, score_breakdown)
        """
        # Build UserProfile if not provided
        if not user_profile:
            user_profile = self._build_profile_from_preferences(user_preferences)

        breakdown = {}

        # 1. Semantic similarity (embedding-based)
        semantic_score = self._score_semantic(market, user_profile, analysis)
        breakdown["semantic"] = semantic_score

        # 2. Category match (keyword-based)
        category_score = self._score_category_match(market, user_profile)
        breakdown["category"] = category_score

        # 3. Risk alignment
        risk_score = self._score_risk_match(market, user_profile, analysis)
        breakdown["risk"] = risk_score

        # 4. Trend/viral signals
        trend_score = self._score_trend(market, analysis, context_tokens)
        breakdown["trend"] = trend_score

        # 5. Volume/liquidity
        volume_score = self._score_volume(market, user_profile)
        breakdown["volume"] = volume_score

        # 6. AI confidence
        confidence_score = self._score_confidence(analysis, user_profile) if analysis else 50.0
        breakdown["confidence"] = confidence_score

        # 7. Sentiment match
        sentiment_score = self._score_sentiment(analysis, user_profile) if analysis else 50.0
        breakdown["sentiment"] = sentiment_score

        # Calculate weighted total
        total = (
            semantic_score * self.weights.semantic +
            category_score * self.weights.category +
            risk_score * self.weights.risk +
            trend_score * self.weights.trend +
            volume_score * self.weights.volume +
            confidence_score * self.weights.confidence +
            sentiment_score * self.weights.sentiment
        )

        return min(100.0, total), breakdown

    def _score_semantic(
        self,
        market: Dict,
        user_profile: UserProfile,
        analysis: Optional[Dict]
    ) -> float:
        """
        Semantic similarity using embeddings or fallback to tag overlap.
        """
        # If embeddings available, use cosine similarity
        if (user_profile.interest_embedding and
            analysis and "embedding" in analysis):
            user_emb = user_profile.interest_embedding
            market_emb = analysis["embedding"]

            similarity = self._cosine_similarity(user_emb, market_emb)
            return (similarity + 1.0) * 50.0  # Map [-1, 1] to [0, 100]

        # Fallback: Jaccard similarity on detected tags
        market_text = f"{market.get('title', '')} {market.get('description', '')}"
        market_tags = set(self.detect_category(market_text))
        user_tags = set(user_profile.categories)

        if not user_tags or not market_tags:
            return 50.0

        intersection = len(market_tags & user_tags)
        union = len(market_tags | user_tags)

        jaccard = intersection / union if union > 0 else 0.0
        return jaccard * 100.0

    def _cosine_similarity(self, vec_a: List[float], vec_b: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        if len(vec_a) != len(vec_b):
            return 0.0

        dot_product = sum(a * b for a, b in zip(vec_a, vec_b))
        norm_a = math.sqrt(sum(a * a for a in vec_a))
        norm_b = math.sqrt(sum(b * b for b in vec_b))

        if norm_a == 0 or norm_b == 0:
            return 0.0

        return dot_product / (norm_a * norm_b)

    def _score_category_match(self, market: Dict, user_profile: UserProfile) -> float:
        """Enhanced category matching with user learning weights"""
        user_categories = user_profile.categories
        if not user_categories:
            return 50.0

        market_text = f"{market.get('category', '')} {market.get('title', '')} {market.get('description', '')}".lower()

        matches = 0
        weighted_matches = 0.0

        for user_cat in user_categories:
            user_cat_lower = user_cat.lower()
            category_weight = user_profile.category_weights.get(user_cat_lower, 1.0)

            # Check keywords
            if user_cat_lower in self.GEN_Z_CATEGORIES:
                keywords = self.GEN_Z_CATEGORIES[user_cat_lower]
                for keyword in keywords:
                    if keyword in market_text:
                        matches += 1
                        weighted_matches += category_weight
                        break

        if matches > 0:
            base_score = min(100.0, (matches / len(user_categories)) * 100)
            weight_boost = min(100.0, (weighted_matches / len(user_categories)) * 100)
            return (base_score * 0.5) + (weight_boost * 0.5)

        return 0.0

    def _score_risk_match(
        self,
        market: Dict,
        user_profile: UserProfile,
        analysis: Optional[Dict]
    ) -> float:
        """Enhanced risk scoring with volatility and liquidity"""
        user_risk = user_profile.get_effective_risk_tolerance()

        # Get market risk from multiple signals
        market_risk_cat = self._determine_market_risk(market, analysis)

        # Perfect match = 100, adjacent = 60, opposite = 20
        risk_order = {"safe": 0, "medium": 1, "degen": 2}
        user_idx = risk_order.get(user_risk, 1)
        market_idx = risk_order.get(market_risk_cat, 1)
        distance = abs(user_idx - market_idx)

        if distance == 0:
            return 100.0
        elif distance == 1:
            return 60.0
        else:
            return 20.0

    def _determine_market_risk(self, market: Dict, analysis: Optional[Dict]) -> str:
        """Determine market risk from multiple signals"""
        signals = []

        # Signal 1: AI analysis risk level
        if analysis and "risk_level" in analysis:
            risk_level = analysis["risk_level"]
            if isinstance(risk_level, str):
                return risk_level.lower()
            elif isinstance(risk_level, (int, float)):
                if risk_level <= 2:
                    signals.append("safe")
                elif risk_level <= 3:
                    signals.append("medium")
                else:
                    signals.append("degen")

        # Signal 2: Odds spread
        odds_yes = market.get("odds_yes", 0.5)
        odds_no = market.get("odds_no", 0.5)
        odds_spread = abs(odds_yes - odds_no)

        if odds_spread > 0.6:
            signals.append("safe")
        elif odds_spread > 0.3:
            signals.append("medium")
        else:
            signals.append("degen")

        # Signal 3: Volatility (if available)
        if analysis and "volatility" in analysis:
            volatility = analysis["volatility"]
            if volatility < 0.2:
                signals.append("safe")
            elif volatility < 0.5:
                signals.append("medium")
            else:
                signals.append("degen")

        # Signal 4: Liquidity
        liquidity = market.get("liquidity", 0)
        if liquidity > 100000:
            signals.append("safe")
        elif liquidity > 10000:
            signals.append("medium")
        else:
            signals.append("degen")

        # Vote: most common signal
        if signals:
            risk_counts = defaultdict(int)
            for sig in signals:
                risk_counts[sig] += 1
            return max(risk_counts.items(), key=lambda x: x[1])[0]

        return "medium"

    def _score_trend(
        self,
        market: Dict,
        analysis: Optional[Dict],
        context_tokens: Optional[Dict[str, float]]
    ) -> float:
        """
        Score trending/viral signals with momentum detection.
        """
        score = 0.0

        # 1. Volume momentum (24h vs 7d)
        vol_24h = market.get("volume_24h", 0)
        vol_7d = market.get("volume_7d", 0)

        if vol_7d > 0:
            momentum = (vol_24h * 7) / vol_7d  # Normalized daily rate
            if momentum > 1.5:  # Growing
                score += 30.0
            elif momentum > 1.0:
                score += 15.0

        # 2. Trader activity
        traders_24h = market.get("traders_24h", 0)
        if traders_24h > 100:
            score += 20.0
        elif traders_24h > 50:
            score += 10.0

        # 3. Price change (volatility can mean trending)
        price_change = abs(market.get("price_change_24h", 0))
        if price_change > 0.15:  # 15%+ change
            score += 20.0
        elif price_change > 0.05:
            score += 10.0

        # 4. Social buzz (from AI analysis)
        if analysis and "social_buzz" in analysis:
            buzz = analysis["social_buzz"]  # 0-1 scale
            score += buzz * 15.0

        # 5. Context tokens (viral events)
        if context_tokens:
            market_text = f"{market.get('title', '')} {market.get('description', '')}".lower()
            for token, weight in context_tokens.items():
                if token.lower() in market_text:
                    score += weight * 15.0
                    break

        return min(100.0, score)

    def _score_volume(self, market: Dict, user_profile: UserProfile) -> float:
        """Score volume/liquidity separately"""
        volume = market.get("volume", 0)
        liquidity = market.get("liquidity", 0)

        min_volume = user_profile.min_volume
        if volume < min_volume:
            return 0.0

        # Volume score (60%)
        if volume >= 1_000_000:
            vol_score = 100.0
        elif volume >= 500_000:
            vol_score = 85.0
        elif volume >= 100_000:
            vol_score = 70.0
        elif volume >= 50_000:
            vol_score = 55.0
        elif volume >= 10_000:
            vol_score = 40.0
        else:
            vol_score = 25.0

        # Liquidity score (40%)
        if liquidity >= 500_000:
            liq_score = 100.0
        elif liquidity >= 100_000:
            liq_score = 80.0
        elif liquidity >= 50_000:
            liq_score = 60.0
        elif liquidity >= 10_000:
            liq_score = 40.0
        else:
            liq_score = 20.0

        return (vol_score * 0.6) + (liq_score * 0.4)

    def _score_confidence(self, analysis: Dict, user_profile: UserProfile) -> float:
        """Score AI confidence"""
        confidence = analysis.get("confidence", 0.5)
        min_confidence = user_profile.min_confidence

        if confidence < min_confidence:
            return 0.0

        return confidence * 100

    def _score_sentiment(self, analysis: Dict, user_profile: UserProfile) -> float:
        """Score sentiment match"""
        sentiment_pref = user_profile.sentiment_preference
        if not sentiment_pref:
            return 50.0

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
        analyses: Optional[Dict[str, Dict]] = None,
        user_profile: Optional[UserProfile] = None,
        context_tokens: Optional[Dict[str, float]] = None,
        k: int = 50,
        diversity_lambda: float = 0.7
    ) -> List[Dict]:
        """
        Rank markets with MMR (Maximal Marginal Relevance) for diversity.

        Args:
            markets: List of markets
            user_preferences: Legacy preferences
            analyses: {market_id: analysis}
            user_profile: Optional UserProfile
            context_tokens: Viral context
            k: Number of results
            diversity_lambda: Balance relevance (1.0) vs diversity (0.0)

        Returns:
            Ranked list with recommendation_score and score_breakdown
        """
        if not user_profile:
            user_profile = self._build_profile_from_preferences(user_preferences)

        # Score all markets
        scored_markets = []
        for market in markets:
            market_id = market.get("id")
            analysis = analyses.get(market_id) if analyses else None

            score, breakdown = self.score_market(
                market, user_preferences, analysis, user_profile, context_tokens
            )

            scored_markets.append({
                **market,
                "recommendation_score": round(score, 2),
                "score_breakdown": breakdown
            })

        # Sort by score
        scored_markets.sort(key=lambda m: m["recommendation_score"], reverse=True)

        # Apply MMR for diversity
        if diversity_lambda < 1.0 and len(scored_markets) > k:
            scored_markets = self._apply_mmr(
                scored_markets, k, diversity_lambda
            )
        else:
            scored_markets = scored_markets[:k]

        return scored_markets

    def _apply_mmr(
        self,
        scored_markets: List[Dict],
        k: int,
        lambda_param: float
    ) -> List[Dict]:
        """
        Maximal Marginal Relevance for diversity.
        Balances relevance vs diversity to avoid repetitive results.
        """
        if len(scored_markets) <= k:
            return scored_markets

        selected = []
        remaining = scored_markets.copy()

        # Always take the top result first
        selected.append(remaining.pop(0))

        while len(selected) < k and remaining:
            best_idx = 0
            best_mmr = -float('inf')

            for idx, candidate in enumerate(remaining):
                # Relevance score
                relevance = candidate["recommendation_score"] / 100.0

                # Diversity: minimum similarity to already selected
                max_similarity = 0.0
                for selected_market in selected:
                    similarity = self._market_similarity(candidate, selected_market)
                    max_similarity = max(max_similarity, similarity)

                # MMR formula
                mmr_score = lambda_param * relevance - (1 - lambda_param) * max_similarity

                if mmr_score > best_mmr:
                    best_mmr = mmr_score
                    best_idx = idx

            selected.append(remaining.pop(best_idx))

        return selected

    def _market_similarity(self, market_a: Dict, market_b: Dict) -> float:
        """Calculate similarity between two markets (for diversity)"""
        # Category similarity
        cat_a = market_a.get("category", "").lower()
        cat_b = market_b.get("category", "").lower()
        cat_match = 1.0 if cat_a == cat_b else 0.0

        # Tag overlap
        tags_a = set(self.detect_category(
            f"{market_a.get('title', '')} {market_a.get('description', '')}"
        ))
        tags_b = set(self.detect_category(
            f"{market_b.get('title', '')} {market_b.get('description', '')}"
        ))

        if tags_a and tags_b:
            jaccard = len(tags_a & tags_b) / len(tags_a | tags_b)
        else:
            jaccard = 0.0

        return (cat_match * 0.5) + (jaccard * 0.5)

    def _build_profile_from_preferences(self, preferences: Dict) -> UserProfile:
        """Convert legacy preferences dict to UserProfile"""
        return UserProfile(
            user_id="anonymous",
            categories=preferences.get("categories", []),
            risk_tolerance=preferences.get("risk_tolerance", "medium"),
            min_volume=preferences.get("min_volume", 0),
            min_confidence=preferences.get("min_confidence", 0.0),
            sentiment_preference=preferences.get("sentiment_preference"),
            interest_embedding=preferences.get("interest_embedding")
        )

    def detect_category(self, text: str) -> List[str]:
        """Detect categories from text with Gen Z slang support"""
        text_lower = text.lower()
        detected = []

        # Check standard categories
        for category, keywords in self.GEN_Z_CATEGORIES.items():
            for keyword in keywords:
                if keyword in text_lower:
                    detected.append(category)
                    break

        # Check Gen Z slang
        for slang, meanings in self.GEN_Z_SLANG.items():
            if slang in text_lower:
                # Map slang to categories (mainly culture)
                if "culture" not in detected:
                    detected.append("culture")
                break

        return list(set(detected))

    def get_trending_markets(
        self,
        markets: List[Dict],
        limit: int = 10,
        context_tokens: Optional[Dict[str, float]] = None
    ) -> List[Dict]:
        """
        Get trending markets with momentum detection.
        """
        scored = []

        for market in markets:
            # Base: volume + liquidity
            volume = market.get("volume", 0)
            liquidity = market.get("liquidity", 0)
            base_score = volume + (liquidity * 0.5)

            # Momentum boost
            vol_24h = market.get("volume_24h", 0)
            vol_7d = market.get("volume_7d", 0)
            if vol_7d > 0:
                momentum = (vol_24h * 7) / vol_7d
                base_score *= max(1.0, momentum)

            # Recency boost (newer = trendier)
            updated_at = market.get("updated_at")
            if updated_at:
                try:
                    if isinstance(updated_at, str):
                        dt = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
                    else:
                        dt = datetime.fromtimestamp(updated_at, tz=timezone.utc)

                    hours_old = (datetime.now(timezone.utc) - dt).total_seconds() / 3600
                    recency_factor = math.exp(-hours_old / 24)  # Decay over 24h
                    base_score *= (1 + recency_factor)
                except:
                    pass

            # Context boost
            if context_tokens:
                market_text = f"{market.get('title', '')} {market.get('description', '')}".lower()
                for token, weight in context_tokens.items():
                    if token.lower() in market_text:
                        base_score *= (1 + weight)
                        break

            scored.append({
                **market,
                "trend_score": base_score
            })

        scored.sort(key=lambda m: m["trend_score"], reverse=True)
        return scored[:limit]


# Global instance
recommendation_engine_v2 = RecommendationEngineV2()
