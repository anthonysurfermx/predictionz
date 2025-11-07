"""
PredictionZ Backend API
FastAPI server with Claude AI + Polymarket integration
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel

from services.claude_analyzer import analyzer
from services.polymarket_client import polymarket_client

# Load environment variables
load_dotenv()

# Initialize FastAPI
app = FastAPI(
    title="PredictionZ API",
    description="AI-powered prediction market analysis using Claude + Polymarket",
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


# Routes
@app.get("/")
async def root():
    """Health check"""
    return {
        "status": "online",
        "service": "PredictionZ API",
        "version": "1.0.0",
        "ai_model": "Claude Sonnet 4.5"
    }


@app.get("/api/markets")
async def get_markets(
    limit: int = 20,
    offset: int = 0,
    active: bool = True
):
    """
    Get list of active prediction markets from Polymarket

    Query params:
    - limit: Number of markets to return (default 20)
    - offset: Pagination offset (default 0)
    - active: Only show active markets (default true)
    """
    try:
        markets = await polymarket_client.get_markets(
            limit=limit,
            offset=offset,
            active=active
        )
        return {
            "success": True,
            "count": len(markets),
            "markets": markets
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
    Get AI analysis for a prediction market using Claude

    Body:
    - condition_id: Market to analyze
    - news_context: Optional list of recent news articles
    """
    try:
        # Get market data
        market = await polymarket_client.get_market_detail(request.condition_id)

        if not market:
            raise HTTPException(status_code=404, detail="Market not found")

        # Run AI analysis
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

        # Add metadata
        analysis["market_id"] = request.condition_id
        analysis["analyzed_at"] = datetime.utcnow().isoformat()

        return {
            "success": True,
            "analysis": analysis
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
