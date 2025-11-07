"""
Claude AI Market Analysis Service
Analyzes Polymarket prediction markets using Claude API
"""
import os
from typing import Dict, List, Optional
from anthropic import Anthropic
import json

class ClaudeAnalyzer:
    """AI-powered market analysis using Claude"""

    def __init__(self):
        self.client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.model = "claude-sonnet-4-5-20250929"  # Latest Claude model

    async def analyze_market(
        self,
        market_title: str,
        market_description: str,
        current_odds: Dict[str, float],
        volume: float,
        recent_news: Optional[List[str]] = None
    ) -> Dict:
        """
        Analyze a prediction market and provide AI insights

        Args:
            market_title: Market question/title
            market_description: Detailed market description
            current_odds: {"YES": 0.65, "NO": 0.35}
            volume: Total trading volume
            recent_news: Optional list of recent news articles

        Returns:
            {
                "confidence": 0.78,
                "prediction": "YES",
                "reasoning": ["Point 1", "Point 2", ...],
                "sentiment": "bullish" | "bearish" | "neutral",
                "risk_level": 1-5,
                "key_factors": ["Factor 1", ...],
                "recommendation": "BUY" | "SELL" | "HOLD"
            }
        """

        # Build context for Claude
        context = f"""
Prediction Market Analysis Request:

MARKET: {market_title}
DESCRIPTION: {market_description}

CURRENT ODDS:
- YES: {current_odds.get('YES', 0):.2%} (${current_odds.get('YES', 0)})
- NO: {current_odds.get('NO', 0):.2%} (${current_odds.get('NO', 0)})

VOLUME: ${volume:,.2f} USDC
"""

        if recent_news:
            context += f"\n\nRECENT NEWS:\n" + "\n".join([f"- {news}" for news in recent_news])

        prompt = f"""{context}

As an expert prediction market analyst, analyze this market and provide:

1. CONFIDENCE (0-100%): How confident are you in the current market odds?
2. PREDICTION: Which outcome (YES or NO) is more likely?
3. REASONING: 3-5 bullet points explaining your analysis
4. SENTIMENT: Overall market sentiment (bullish/bearish/neutral)
5. RISK LEVEL: Rate 1-5 skulls (💀) where 5 is highest risk
6. KEY FACTORS: Main factors influencing this market
7. RECOMMENDATION: Should traders BUY, SELL, or HOLD?

Use Gen Z language style: casual, authentic, direct. Use phrases like "no cap", "fr fr", emojis.

Respond ONLY with valid JSON in this exact format:
{{
    "confidence": 0.78,
    "prediction": "YES",
    "reasoning": [
        "Point 1 explaining why...",
        "Point 2 with evidence...",
        "Point 3 about risk factors..."
    ],
    "sentiment": "bullish",
    "risk_level": 3,
    "key_factors": [
        "Factor 1",
        "Factor 2"
    ],
    "recommendation": "BUY",
    "gen_z_take": "Short punchy summary using Gen Z language"
}}
"""

        try:
            # Call Claude API
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2048,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            # Parse response
            content = response.content[0].text
            analysis = json.loads(content)

            # Add metadata
            analysis["analyzed_at"] = None  # Will be set by caller
            analysis["model"] = self.model

            return analysis

        except json.JSONDecodeError as e:
            # Fallback if Claude doesn't return valid JSON
            return {
                "confidence": 0.5,
                "prediction": "UNCERTAIN",
                "reasoning": ["Unable to analyze market at this time"],
                "sentiment": "neutral",
                "risk_level": 3,
                "key_factors": [],
                "recommendation": "HOLD",
                "gen_z_take": "AI needs more data fr",
                "error": str(e)
            }
        except Exception as e:
            print(f"Claude analysis error: {e}")
            return {
                "confidence": 0.5,
                "prediction": "UNCERTAIN",
                "reasoning": ["Analysis failed"],
                "sentiment": "neutral",
                "risk_level": 3,
                "key_factors": [],
                "recommendation": "HOLD",
                "gen_z_take": "Something went wrong 💀",
                "error": str(e)
            }

    async def get_trading_signal(
        self,
        analysis: Dict,
        user_position: Optional[Dict] = None
    ) -> Dict:
        """
        Generate trading signal based on analysis

        Args:
            analysis: Output from analyze_market()
            user_position: Optional current user position

        Returns:
            {
                "signal": "STRONG_BUY" | "BUY" | "HOLD" | "SELL" | "STRONG_SELL",
                "entry_price": 0.65,
                "stop_loss": 0.55,
                "take_profit": 0.85,
                "position_size": "Suggested % of portfolio"
            }
        """

        confidence = analysis.get("confidence", 0.5)
        prediction = analysis.get("prediction", "UNCERTAIN")
        risk_level = analysis.get("risk_level", 3)

        # Generate signal based on confidence and risk
        if confidence >= 0.8 and risk_level <= 2:
            signal = "STRONG_BUY" if prediction == "YES" else "STRONG_SELL"
        elif confidence >= 0.65:
            signal = "BUY" if prediction == "YES" else "SELL"
        else:
            signal = "HOLD"

        return {
            "signal": signal,
            "confidence": confidence,
            "risk_level": risk_level,
            "reasoning": analysis.get("gen_z_take", "")
        }

    async def compare_markets(
        self,
        markets: List[Dict]
    ) -> Dict:
        """
        Compare multiple markets and rank by opportunity

        Args:
            markets: List of market dictionaries

        Returns:
            Ranked list with scores
        """

        prompt = f"""
Compare these {len(markets)} prediction markets and rank them by opportunity score (0-100).

MARKETS:
{json.dumps(markets, indent=2)}

Return JSON array sorted by opportunity (best first):
[
    {{
        "market_id": "...",
        "opportunity_score": 85,
        "why": "Quick explanation"
    }},
    ...
]
"""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2048,
                messages=[{"role": "user", "content": prompt}]
            )

            return json.loads(response.content[0].text)
        except Exception as e:
            print(f"Market comparison error: {e}")
            return []


# Initialize singleton
analyzer = ClaudeAnalyzer()
