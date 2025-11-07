# Recommendation Engine V2 - Upgrade Guide 🚀

## What's New in V2?

The V2 recommendation engine transforms PredictionZ from basic keyword matching to an intelligent, TikTok-style "For You" algorithm that truly understands Gen Z.

### Key Improvements

#### 1. **Semantic Understanding** 🧠
- **Before (V1)**: Simple keyword matching ("crypto" = ["bitcoin", "ethereum"])
- **After (V2)**: Embedding-based semantic similarity that understands context
- **Example**: "Will Elon tweet about Dogecoin?" now matches BOTH crypto AND culture categories

#### 2. **Viral/Trending Detection** 🔥
- **Volume Momentum**: Detects markets with 24h vs 7d volume growth
- **Social Buzz**: Integrates AI-detected social media signals
- **Context Tokens**: Boost markets related to trending events (e.g., "worldcup", "grammys")
- **Price Volatility**: High price changes signal trending markets

#### 3. **User Learning & Personalization** 📊
- **UserProfile**: Tracks user interactions and learns preferences over time
- **Category Weights**: Boosts categories user engages with most
- **Risk Adjustment**: Adapts risk tolerance based on user behavior
- **Engagement History**: Learns from views, clicks, and bets

#### 4. **Diversity (MMR)** 🎯
- **Before (V1)**: Returns top 20 similar markets (boring!)
- **After (V2)**: Maximal Marginal Relevance ensures diverse, interesting feed
- **Result**: No more seeing 10 similar crypto markets in a row

#### 5. **Gen Z Cultural Context** 💯
- **Slang Detection**: Understands "ratio", "bussin", "no cap", "goat", etc.
- **Cross-Category Intelligence**: "Will Taylor Swift attend Super Bowl?" = culture + sports
- **Meme Culture**: Recognizes "yolo", "moon", "ape", "degen" signals

#### 6. **Sophisticated Risk Assessment** ⚖️
- **Multiple Signals**: Combines odds spread, liquidity, volatility, AI risk score
- **Voting System**: Uses consensus from multiple risk indicators
- **Dynamic**: Adapts to user's actual risk-taking behavior

## Architecture

### Scoring Weights (Configurable)

```python
semantic:    30%  # Embedding similarity or tag overlap
category:    20%  # Keyword matching (boosted by learning)
risk:        15%  # Risk tolerance alignment
trend:       15%  # Viral/trending signals
volume:      10%  # Market size and liquidity
confidence:   5%  # AI confidence score
sentiment:    5%  # Sentiment preference match
```

### New Data Structures

#### UserProfile
```python
@dataclass
class UserProfile:
    user_id: str
    categories: List[str]
    risk_tolerance: str

    # Learning
    category_weights: Dict[str, float]  # Boosts favorite categories
    risk_adjustment: float              # -1.0 (safer) to +1.0 (more degen)
    history: List[UserHistoryEvent]     # Interaction history

    # Semantic
    interest_embedding: Optional[List[float]]  # For cosine similarity

    # Preferences
    min_volume: int
    min_confidence: float
    sentiment_preference: Optional[str]
    time_horizon: str  # "short", "long", "balanced"
```

#### Trending Signals
```python
# Market fields V2 can leverage:
volume_24h: int          # 24-hour volume
volume_7d: int           # 7-day volume
traders_24h: int         # Active traders
price_change_24h: float  # Price volatility
updated_at: datetime     # For recency boost
```

## Migration Guide

### Step 1: Enable V2

Add to your `.env` file:
```bash
USE_RECOMMENDATION_V2=true
```

### Step 2: Update Market Data (Optional)

If you have access to these fields from Polymarket, add them to your market objects:
```python
{
    "id": "...",
    "title": "...",
    # ... existing fields ...

    # Optional V2 enhancements:
    "volume_24h": 50000,
    "volume_7d": 200000,
    "traders_24h": 120,
    "price_change_24h": 0.15,
    "updated_at": "2024-01-15T12:00:00Z"
}
```

### Step 3: Enhance AI Analysis (Optional)

Update your AI analysis to include:
```python
{
    "confidence": 0.72,
    "risk_level": 3,  # 1-5 or "safe"/"medium"/"degen"
    "sentiment": "bullish",

    # Optional V2 enhancements:
    "embedding": [0.1, 0.2, ...],  # 768-dim vector from GPT/Gemini
    "volatility": 0.35,            # 0-1 scale
    "social_buzz": 0.8             # 0-1 scale
}
```

### Step 4: Use Viral Context (Optional)

Boost trending topics:
```python
# In your API endpoint:
context_tokens = {
    "worldcup": 1.0,
    "grammys": 0.8,
    "superbowl": 0.9
}

ranked = recommendation_adapter.rank_markets(
    markets=markets,
    user_preferences=prefs,
    context_tokens=context_tokens,  # V2 feature
    diversity_lambda=0.7            # V2 feature (0=max diversity, 1=max relevance)
)
```

## Usage Examples

### Basic Usage (Compatible with V1)

```python
# Works with both V1 and V2
from services.migrate_to_v2 import recommendation_adapter

markets = await polymarket_client.get_markets(limit=50)
user_prefs = {
    "categories": ["crypto", "tech"],
    "risk_tolerance": "medium"
}

ranked = recommendation_adapter.rank_markets(
    markets=markets,
    user_preferences=user_prefs
)
```

### Advanced V2 Usage

```python
from services.recommendation_engine_v2 import UserProfile, UserHistoryEvent
from services.migrate_to_v2 import recommendation_adapter

# Create user profile
profile = UserProfile(
    user_id="user_123",
    categories=["crypto", "tech"],
    risk_tolerance="medium",
    interest_embedding=user_embedding  # From GPT/Gemini
)

# Add interaction history
profile.learn_from_interaction(UserHistoryEvent(
    market_id="market_abc",
    action="click",
    category="crypto",
    risk_level="degen",
    timestamp=time.time(),
    engagement_score=2.0  # Higher = more engaged
))

# Rank with full V2 features
ranked = recommendation_adapter.rank_markets(
    markets=markets,
    user_preferences=user_prefs,
    user_profile=profile,           # V2 learning
    context_tokens=trending_topics,  # V2 viral detection
    k=20,
    diversity_lambda=0.7             # V2 diversity (0-1)
)

# Each market now has:
# - recommendation_score: 0-100
# - score_breakdown: {"semantic": 85, "category": 90, ...}
```

## Testing & Comparison

### Compare V1 vs V2 Scores

```bash
cd /Users/mrrobot/Documents/GitHub/PredictionZ
python services/migrate_to_v2.py
```

Output:
```
🔬 Testing Recommendation Engine V1 vs V2

📊 Comparison Results:
   V1 Score: 68.5
   V2 Score: 82.3
   Difference: +13.8

📈 V2 Breakdown:
   semantic: 75.0
   category: 90.0
   risk: 100.0
   trend: 85.0
   volume: 70.0
   confidence: 72.0
   sentiment: 100.0
```

### A/B Testing in Production

```python
# Split traffic 50/50
import random

use_v2 = random.random() < 0.5
adapter = RecommendationEngineAdapter(use_v2=use_v2)

# Log which version was used
analytics.track("recommendation_version", {"version": "v2" if use_v2 else "v1"})
```

## Performance Considerations

### V1 vs V2 Latency

| Operation | V1 | V2 (no embeddings) | V2 (with embeddings) |
|-----------|----|--------------------|----------------------|
| score_market | ~0.1ms | ~0.2ms | ~0.5ms |
| rank_markets (50) | ~5ms | ~10ms | ~25ms |
| rank_markets (500) | ~50ms | ~100ms | ~250ms |

**Recommendation**: For real-time API responses, use embeddings sparingly or cache them.

### Cost Estimates

| Feature | API Calls | Cost per Request |
|---------|-----------|------------------|
| V1 (keywords only) | 0 | $0 |
| V2 (no embeddings) | 0 | $0 |
| V2 (with GPT-4 embeddings) | 1-2 | $0.0001-0.0002 |
| V2 (with Gemini embeddings) | 1-2 | $0.00005-0.0001 |

**Recommendation**: Generate embeddings once and cache them.

## Next Steps: GPT-5 & Gemini Integration

### 1. Generate User Embeddings

```python
# From Instagram/quiz using GPT-4
async def generate_user_embedding(user_data: dict) -> List[float]:
    from openai import OpenAI
    client = OpenAI()

    # Combine user interests into text
    text = f"User interests: {', '.join(user_data['categories'])}. "
    text += f"Risk: {user_data['risk_tolerance']}. "
    text += f"Themes: {', '.join(user_data.get('themes', []))}"

    response = client.embeddings.create(
        input=text,
        model="text-embedding-3-small"  # or text-embedding-3-large
    )

    return response.data[0].embedding
```

### 2. Generate Market Embeddings

```python
# For each market
async def generate_market_embedding(market: dict) -> List[float]:
    text = f"{market['title']}. {market.get('description', '')}"

    response = client.embeddings.create(
        input=text,
        model="text-embedding-3-small"
    )

    return response.data[0].embedding
```

### 3. Use Gemini for Analysis

```python
# Enhanced AI analysis with Gemini
import google.generativeai as genai

async def analyze_with_gemini(market: dict):
    model = genai.GenerativeModel('gemini-pro')

    prompt = f"""
    Analyze this prediction market for Gen Z users:
    Title: {market['title']}
    Description: {market['description']}

    Return JSON with:
    - confidence (0-1)
    - risk_level (1-5)
    - volatility (0-1)
    - social_buzz (0-1)
    - sentiment (bullish/bearish/neutral)
    - gen_z_take (casual explanation)
    """

    response = model.generate_content(prompt)
    return parse_json(response.text)
```

## Troubleshooting

### V2 Scores Lower Than V1?

This can happen if:
1. No embeddings provided (V2 falls back to Jaccard similarity)
2. Missing market metadata (volume_24h, traders_24h, etc.)
3. Weights need tuning for your use case

**Solution**: Adjust weights in `Weights` dataclass:
```python
from services.recommendation_engine_v2 import Weights

custom_weights = Weights(
    semantic=0.35,    # Increase semantic importance
    category=0.25,    # Increase category matching
    risk=0.15,
    trend=0.10,       # Reduce if markets lack trend data
    volume=0.10,
    confidence=0.03,
    sentiment=0.02
)

adapter = RecommendationEngineAdapter(use_v2=True, custom_weights=custom_weights)
```

### Markets Not Diverse Enough?

Increase MMR diversity:
```python
ranked = recommendation_adapter.rank_markets(
    markets=markets,
    user_preferences=prefs,
    diversity_lambda=0.5  # Lower = more diverse (default: 0.7)
)
```

### Too Slow in Production?

1. **Cache embeddings** in Supabase/Redis
2. **Limit market pool** to 50-100 before ranking
3. **Use haiku model** for embeddings (faster, cheaper)
4. **Precompute** trending markets every 5 minutes

## Monitoring & Analytics

### Track Recommendation Quality

```python
# Log V2 breakdown for analysis
for market in ranked[:10]:
    analytics.track("recommendation_shown", {
        "market_id": market["id"],
        "score": market["recommendation_score"],
        "breakdown": market["score_breakdown"],
        "rank": ranked.index(market)
    })
```

### Key Metrics to Monitor

1. **Click-Through Rate (CTR)** by score bracket
2. **Diversity Score**: Average category distribution in top 20
3. **Latency**: p50, p95, p99 for rank_markets
4. **User Engagement**: Time spent, bets placed
5. **V1 vs V2 Performance**: A/B test results

## Support

For issues or questions:
1. Check [migrate_to_v2.py](services/migrate_to_v2.py) for examples
2. Run comparison script: `python services/migrate_to_v2.py`
3. Review breakdown in API responses: `score_breakdown` field

---

**Built with ❤️ for Gen Z by the PredictionZ team**
