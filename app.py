"""
PredictionZ Backend API
FastAPI server with OpenAI GPT-4 + Polymarket integration
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel

from services.openai_analyzer import analyzer
from services.polymarket_client import polymarket_client
from services.supabase_sync import supabase_sync
from services.recommendation_engine import recommendation_engine
from services.instagram_analyzer import instagram_analyzer
from services.embedding_service import embedding_service
from services.viral_context_service import viral_context_service, get_current_viral_context
from services.migrate_to_v2 import (
    recommendation_adapter,
    create_profile_from_instagram,
    create_profile_from_quiz
)

# Load environment variables
load_dotenv()

# Feature flag: Use V2 recommendation engine
USE_RECOMMENDATION_V2 = os.getenv("USE_RECOMMENDATION_V2", "false").lower() == "true"

# Set the adapter to use V2 if enabled
if USE_RECOMMENDATION_V2:
    print("✨ Using Recommendation Engine V2 (with semantic matching & viral detection)")
    recommendation_adapter.use_v2 = True
else:
    print("📊 Using Recommendation Engine V1 (classic keyword matching)")
    recommendation_adapter.use_v2 = False

# Initialize FastAPI
app = FastAPI(
    title="PredictionZ API",
    description="AI-powered prediction market analysis using OpenAI GPT-4 + Polymarket",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update with your Vercel domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response Models
class AnalyzeMarketRequest(BaseModel):
    condition_id: str
    news_context: Optional[List[str]] = None

class AnalysisResponse(BaseModel):
    market_id: str
    confidence: float
    prediction: str
    reasoning: List[str]
    sentiment: str
    risk_level: int
    key_factors: List[str]
    recommendation: str
    gen_z_take: str
    analyzed_at: str

class UserPreferences(BaseModel):
    categories: Optional[List[str]] = []
    risk_tolerance: Optional[str] = "medium"  # "safe", "medium", "degen"
    min_confidence: Optional[float] = 0.0
    min_volume: Optional[float] = 0.0
    sentiment_preference: Optional[str] = None  # "bullish", "bearish", "neutral"

class RecommendRequest(BaseModel):
    preferences: UserPreferences
    limit: Optional[int] = 20

class InstagramAnalyzeRequest(BaseModel):
    username: str


# Routes
@app.get("/")
async def root():
    """Health check"""
    return {
        "status": "online",
        "service": "PredictionZ API",
        "version": "1.0.0",
        "ai_model": "GPT-4 Turbo"
    }


@app.get("/api/markets")
async def get_markets(
    limit: int = 20,
    offset: int = 0,
    active: bool = True,
    sync: bool = True
):
    """
    Get list of active prediction markets from Polymarket

    Query params:
    - limit: Number of markets to return (default 20)
    - offset: Pagination offset (default 0)
    - active: Only show active markets (default true)
    - sync: Sync from Polymarket to Supabase (default true)
    """
    try:
        if sync:
            # Fetch from Polymarket and sync to Supabase
            polymarket_markets = await polymarket_client.get_markets(
                limit=limit,
                offset=offset,
                active=active
            )

            # Sync to Supabase
            await supabase_sync.sync_markets_batch(polymarket_markets)

            return {
                "success": True,
                "count": len(polymarket_markets),
                "markets": polymarket_markets,
                "synced": True
            }
        else:
            # Just fetch from Supabase
            markets = await supabase_sync.get_markets(
                limit=limit,
                offset=offset,
                status="active" if active else "all"
            )

            return {
                "success": True,
                "count": len(markets),
                "markets": markets,
                "synced": False
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/markets/{condition_id}")
async def get_market_detail(condition_id: str):
    """
    Get detailed information about a specific market

    Path params:
    - condition_id: Polymarket condition ID
    """
    try:
        market = await polymarket_client.get_market_detail(condition_id)

        if not market:
            raise HTTPException(status_code=404, detail="Market not found")

        return {
            "success": True,
            "market": market
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/analyze")
async def analyze_market(request: AnalyzeMarketRequest):
    """
    Get AI analysis for a prediction market using OpenAI GPT-4

    Body:
    - condition_id: Market to analyze
    - news_context: Optional list of recent news articles
    """
    try:
        # Check if we have recent analysis in Supabase
        existing_analysis = await supabase_sync.get_latest_analysis(request.condition_id)

        # If analysis is less than 1 hour old, return it
        if existing_analysis:
            analyzed_at = datetime.fromisoformat(existing_analysis["analyzed_at"])
            age_hours = (datetime.utcnow() - analyzed_at).total_seconds() / 3600

            if age_hours < 1:
                return {
                    "success": True,
                    "analysis": existing_analysis,
                    "cached": True
                }

        # Get market data from Polymarket
        market = await polymarket_client.get_market_detail(request.condition_id)

        if not market:
            raise HTTPException(status_code=404, detail="Market not found")

        # Sync market to Supabase
        await supabase_sync.sync_market(market)

        # Run AI analysis with OpenAI GPT-4
        analysis = await analyzer.analyze_market(
            market_title=market["title"],
            market_description=market["description"],
            current_odds={
                "YES": market["odds_yes"],
                "NO": market["odds_no"]
            },
            volume=market["volume"],
            recent_news=request.news_context
        )

        # Save analysis to Supabase
        analysis_id = await supabase_sync.save_ai_analysis(
            market_id=request.condition_id,
            analysis=analysis
        )

        # Add metadata
        analysis["id"] = analysis_id
        analysis["market_id"] = request.condition_id
        analysis["analyzed_at"] = datetime.utcnow().isoformat()

        return {
            "success": True,
            "analysis": analysis,
            "cached": False
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/markets/{condition_id}/analysis")
async def get_market_analysis(condition_id: str):
    """
    Get AI analysis for a market (convenience endpoint)
    """
    return await analyze_market(AnalyzeMarketRequest(condition_id=condition_id))


@app.get("/api/search")
async def search_markets(q: str):
    """
    Search markets by keyword

    Query params:
    - q: Search query
    """
    try:
        if not q or len(q) < 2:
            raise HTTPException(status_code=400, detail="Query must be at least 2 characters")

        markets = await polymarket_client.search_markets(q)

        return {
            "success": True,
            "query": q,
            "count": len(markets),
            "markets": markets
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/orderbook/{token_id}")
async def get_orderbook(token_id: str):
    """
    Get orderbook for a specific outcome token

    Path params:
    - token_id: YES or NO token ID
    """
    try:
        orderbook = await polymarket_client.get_orderbook(token_id)

        return {
            "success": True,
            "token_id": token_id,
            "orderbook": orderbook
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/trades/{condition_id}")
async def get_market_trades(condition_id: str, limit: int = 50):
    """
    Get recent trades for a market

    Path params:
    - condition_id: Market condition ID

    Query params:
    - limit: Number of trades (default 50)
    """
    try:
        trades = await polymarket_client.get_market_trades(condition_id, limit)

        return {
            "success": True,
            "market_id": condition_id,
            "count": len(trades),
            "trades": trades
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/recommend")
async def get_recommendations(request: RecommendRequest):
    """
    Get personalized market recommendations based on user preferences

    Body:
    - preferences: User preferences object
        - categories: List of interest categories ["crypto", "politics", "tech"]
        - risk_tolerance: "safe", "medium", or "degen"
        - min_confidence: Minimum AI confidence (0.0-1.0)
        - min_volume: Minimum market volume ($)
        - sentiment_preference: "bullish", "bearish", or "neutral"
    - limit: Max markets to return (default 20)
    """
    try:
        # Get markets from Polymarket
        # Try to get more markets to find recent ones
        all_markets = await polymarket_client.get_markets(
            limit=200,  # Get many more to filter through old ones
            offset=0,
            active=True
        )

        # Filter for recent markets (strict: must have valid end_date within 180 days)
        from datetime import timedelta
        now = datetime.now(datetime.now().astimezone().tzinfo)
        window_start = now - timedelta(days=30)  # Started within last 30 days
        window_end = now + timedelta(days=180)   # Ends within next 180 days

        markets = []
        old_year_keywords = ["2020", "2021", "2022", "2023"]

        # First pass: ONLY markets with valid end_date in the future
        for market in all_markets:
            title = market.get("title", "").lower()
            if any(year in title for year in old_year_keywords):
                continue

            end_date = market.get("end_date")
            if end_date:
                try:
                    market_date = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                    # ONLY future markets or very recent past
                    if market_date >= window_start and market_date <= window_end:
                        markets.append(market)
                except:
                    pass  # Skip if can't parse date

        # If still not enough, include markets with high volume regardless of date
        if len(markets) < 10:
            for market in all_markets:
                if market in markets:
                    continue
                title = market.get("title", "").lower()
                if any(year in title for year in old_year_keywords):
                    continue
                # Only very high volume as last resort
                if market.get("volume", 0) > 100000:  # $100K+
                    markets.append(market)
                    if len(markets) >= 20:
                        break

        markets = markets[:50]

        # Convert preferences to dict
        preferences_dict = request.preferences.dict()

        # Create user profile if using V2
        user_profile = None
        context_tokens = None

        if USE_RECOMMENDATION_V2:
            # Generate user embedding for semantic matching
            user_embedding = await embedding_service.generate_user_embedding(
                categories=preferences_dict.get("categories", []),
                risk_tolerance=preferences_dict.get("risk_tolerance", "medium")
            )
            preferences_dict["interest_embedding"] = user_embedding

            # Create user profile
            user_profile = create_profile_from_quiz(
                user_preferences=preferences_dict,
                user_id="anonymous"
            )
            user_profile.interest_embedding = user_embedding

            # Get viral context for trending boost
            context_tokens = get_current_viral_context()

        # Rank markets by recommendation score
        ranked_markets = recommendation_adapter.rank_markets(
            markets=markets,
            user_preferences=preferences_dict,
            user_profile=user_profile,
            context_tokens=context_tokens,  # V2: viral detection
            k=request.limit,
            diversity_lambda=0.7  # V2: diversity
        )

        # Apply limit (for V1 compatibility)
        top_markets = ranked_markets[:request.limit]

        return {
            "success": True,
            "count": len(top_markets),
            "markets": top_markets,
            "preferences": preferences_dict
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/trending")
async def get_trending_markets(limit: int = 10):
    """
    Get trending markets based on volume and activity

    Query params:
    - limit: Max markets to return (default 10)
    """
    try:
        # Get active markets
        markets = await polymarket_client.get_markets(
            limit=50,
            offset=0,
            active=True
        )

        # Get viral context for V2
        context_tokens = None
        if USE_RECOMMENDATION_V2:
            context_tokens = get_current_viral_context()

        # Get trending (V2 supports context_tokens for viral detection)
        trending = recommendation_adapter.get_trending_markets(
            markets=markets,
            limit=limit,
            context_tokens=context_tokens  # V2: boost viral markets
        )

        return {
            "success": True,
            "count": len(trending),
            "markets": trending
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/categories")
async def get_categories():
    """
    Get available categories for filtering and preferences

    Returns list of Gen Z-friendly category tags
    """
    return {
        "success": True,
        "categories": [
            {
                "id": "politics",
                "label": "Politics",
                "emoji": "🏛️",
                "description": "Elections, government, current events"
            },
            {
                "id": "crypto",
                "label": "Crypto",
                "emoji": "₿",
                "description": "Bitcoin, Ethereum, DeFi, NFTs"
            },
            {
                "id": "tech",
                "label": "Tech",
                "emoji": "💻",
                "description": "Startups, AI, Silicon Valley"
            },
            {
                "id": "sports",
                "label": "Sports",
                "emoji": "🏀",
                "description": "NFL, NBA, FIFA, Olympics"
            },
            {
                "id": "culture",
                "label": "Culture",
                "emoji": "🎭",
                "description": "Music, movies, celebrity, viral"
            },
            {
                "id": "finance",
                "label": "Finance",
                "emoji": "📈",
                "description": "Stocks, economy, recession, inflation"
            },
            {
                "id": "degen",
                "label": "Degen",
                "emoji": "🎲",
                "description": "Meme bets, longshots, moonshots"
            }
        ],
        "risk_levels": [
            {
                "id": "safe",
                "label": "Safe Plays",
                "emoji": "🛡️",
                "description": "High probability, low risk"
            },
            {
                "id": "medium",
                "label": "Balanced",
                "emoji": "⚖️",
                "description": "Moderate risk/reward"
            },
            {
                "id": "degen",
                "label": "Degen Mode",
                "emoji": "🚀",
                "description": "High risk, moon potential"
            }
        ]
    }


@app.post("/api/analyze-instagram")
async def analyze_instagram(request: InstagramAnalyzeRequest):
    """
    Analyze Instagram profile and get personalized recommendations

    Body:
    - username: Instagram username (without @)
    """
    try:
        username = request.username.strip().replace("@", "")

        if not username:
            raise HTTPException(status_code=400, detail="Username is required")

        # Get mock posts (in production, this would fetch real posts)
        posts = await instagram_analyzer.get_mock_posts(username)

        # Analyze profile with AI
        analysis = await instagram_analyzer.analyze_profile(username, posts)

        # Convert analysis to preferences
        preferences = {
            "categories": analysis["categories"],
            "risk_tolerance": analysis["risk_tolerance"],
            "min_confidence": 0.0,
            "min_volume": 0,
            "sentiment_preference": None,
            "interest_embedding": analysis.get("embedding")  # V2: from Instagram analyzer
        }

        # Get market recommendations based on preferences
        all_markets = await polymarket_client.get_markets(
            limit=200,  # Get many more to filter through old ones
            offset=0,
            active=True
        )

        # Filter markets within 90 days window (90 days before to 90 days after today)
        from datetime import timedelta
        now = datetime.now(datetime.now().astimezone().tzinfo)
        window_start = now - timedelta(days=90)
        window_end = now + timedelta(days=90)

        markets = []
        # Keywords that indicate very old markets (focus on years only)
        old_year_keywords = ["2020", "2021", "2022", "2023"]

        for market in all_markets:
            # Skip if title contains old years
            title = market.get("title", "").lower()
            if any(year in title for year in old_year_keywords):
                continue

            end_date = market.get("end_date")
            if end_date:
                try:
                    # Parse end date (ISO format: 2024-12-31T23:59:59Z)
                    market_date = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                    # Only include if within 90-day window
                    if window_start <= market_date <= window_end:
                        markets.append(market)
                except:
                    # If parsing fails, include if has decent volume (likely recent)
                    if market.get("volume", 0) > 5000:
                        markets.append(market)
            else:
                # If no end_date, include only if has significant recent activity
                if market.get("volume", 0) > 10000:
                    markets.append(market)

        # Limit to 50 recent markets for recommendation
        markets = markets[:50]

        # Create user profile for V2 (if enabled)
        user_profile = None
        context_tokens = None

        if USE_RECOMMENDATION_V2:
            user_profile = create_profile_from_instagram(
                username=username,
                instagram_analysis=analysis,
                user_id=username
            )
            # Instagram analyzer already added embedding
            user_profile.interest_embedding = analysis.get("embedding")

            # Get viral context
            context_tokens = get_current_viral_context()

        # Rank markets
        ranked_markets = recommendation_adapter.rank_markets(
            markets=markets,
            user_preferences=preferences,
            user_profile=user_profile,
            context_tokens=context_tokens,  # V2: viral detection
            k=20,
            diversity_lambda=0.7
        )

        # Add match reasons
        for market in ranked_markets[:20]:
            market["match_score"] = int(market.get("recommendation_score", 0))
            market["match_reason"] = f"Matches your interests: {', '.join(analysis['categories'][:2])}"

        return {
            "success": True,
            "username": username,
            "analysis": {
                "categories": analysis["categories"],
                "risk_tolerance": analysis["risk_tolerance"],
                "themes": analysis.get("themes", []),
                "reasoning": analysis.get("reasoning", "")
            },
            "markets": ranked_markets[:20]
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error analyzing Instagram: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Run server
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=port,
        reload=True
    )
