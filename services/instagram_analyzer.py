"""
Instagram Profile Analyzer
Analyzes Instagram posts to determine user interests and recommend markets
"""
import os
from typing import List, Dict, Optional
from openai import OpenAI
from services.embedding_service import embedding_service

class InstagramAnalyzer:
    """
    Analyzes Instagram profiles to extract interests and match with prediction markets
    """

    def __init__(self):
        """Initialize the Instagram analyzer with OpenAI"""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")

        self.client = OpenAI(api_key=api_key)

    async def analyze_profile(self, username: str, posts_data: List[Dict]) -> Dict:
        """
        Analyze Instagram profile based on recent posts

        Args:
            username: Instagram username
            posts_data: List of post data (captions, hashtags, etc)

        Returns:
            Dict with detected interests and preferences
        """

        # Extract text content from posts
        captions = []
        hashtags = []

        for post in posts_data:
            if post.get("caption"):
                captions.append(post["caption"])
            if post.get("hashtags"):
                hashtags.extend(post["hashtags"])

        # Create analysis prompt
        prompt = self._create_analysis_prompt(username, captions, hashtags)

        try:
            response = self.client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at analyzing social media content to understand user interests and preferences. You help match users with relevant prediction markets."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=1000
            )

            # Parse response
            analysis_text = response.choices[0].message.content

            # Extract structured data from response
            interests = self._extract_interests(analysis_text)

            # Generate embedding for semantic matching
            embedding = await embedding_service.generate_user_embedding(
                categories=interests.get("categories", []),
                risk_tolerance=interests.get("risk_tolerance", "medium"),
                themes=interests.get("themes", []),
                instagram_captions=captions
            )

            return {
                "username": username,
                "interests": interests,
                "categories": interests.get("categories", []),
                "risk_tolerance": interests.get("risk_tolerance", "medium"),
                "themes": interests.get("themes", []),
                "embedding": embedding,
                "raw_analysis": analysis_text
            }

        except Exception as e:
            print(f"Error analyzing Instagram profile: {e}")
            raise

    def _create_analysis_prompt(self, username: str, captions: List[str], hashtags: List[str]) -> str:
        """
        Create prompt for GPT-4 to analyze Instagram content
        """
        captions_text = "\n".join([f"- {cap[:200]}" for cap in captions[:10]])  # Limit length
        hashtags_text = ", ".join(list(set(hashtags))[:50])  # Unique hashtags, limited

        prompt = f"""Analyze this Instagram profile (@{username}) to determine the user's interests and recommend prediction market categories.

RECENT POST CAPTIONS:
{captions_text if captions_text else "No captions available"}

HASHTAGS USED:
{hashtags_text if hashtags_text else "No hashtags available"}

Based on this content, determine:

1. CATEGORIES (choose all that apply from this list):
   - politics (elections, government, current events)
   - crypto (bitcoin, ethereum, defi, nfts, web3)
   - tech (startups, AI, gadgets, silicon valley)
   - sports (nfl, nba, soccer, olympics)
   - culture (music, movies, celebrity, viral trends)
   - finance (stocks, economy, business)
   - degen (meme culture, high-risk interests)

2. RISK TOLERANCE (choose one):
   - safe (conservative, analytical, data-driven)
   - medium (balanced, moderate risk-taker)
   - degen (high-risk, meme culture, yolo mentality)

3. KEY THEMES: List 3-5 specific topics this person is interested in

Respond in this exact format:
CATEGORIES: [comma-separated list]
RISK: [safe/medium/degen]
THEMES: [comma-separated list]
REASONING: [2-3 sentences explaining your analysis]"""

        return prompt

    def _extract_interests(self, analysis_text: str) -> Dict:
        """
        Extract structured interests from GPT-4 response
        """
        interests = {
            "categories": [],
            "risk_tolerance": "medium",
            "themes": [],
            "reasoning": ""
        }

        lines = analysis_text.split("\n")

        for line in lines:
            line = line.strip()

            if line.startswith("CATEGORIES:"):
                # Extract categories
                cats_text = line.replace("CATEGORIES:", "").strip()
                categories = [c.strip().lower() for c in cats_text.split(",")]
                # Validate against known categories
                valid_cats = ["politics", "crypto", "tech", "sports", "culture", "finance", "degen"]
                interests["categories"] = [c for c in categories if c in valid_cats]

            elif line.startswith("RISK:"):
                # Extract risk tolerance
                risk_text = line.replace("RISK:", "").strip().lower()
                if risk_text in ["safe", "medium", "degen"]:
                    interests["risk_tolerance"] = risk_text

            elif line.startswith("THEMES:"):
                # Extract themes
                themes_text = line.replace("THEMES:", "").strip()
                interests["themes"] = [t.strip() for t in themes_text.split(",")]

            elif line.startswith("REASONING:"):
                # Extract reasoning
                interests["reasoning"] = line.replace("REASONING:", "").strip()

        # Default to at least one category
        if not interests["categories"]:
            interests["categories"] = ["culture"]  # Default fallback

        return interests

    async def get_mock_posts(self, username: str) -> List[Dict]:
        """
        Get mock Instagram posts for testing
        In production, this would call Instagram API
        """
        # Mock data for testing
        mock_posts = [
            {
                "caption": "Just bought more $ETH, feeling bullish on crypto! 🚀",
                "hashtags": ["crypto", "ethereum", "defi", "web3"],
            },
            {
                "caption": "New tech gadget review coming soon! AI is changing everything",
                "hashtags": ["tech", "ai", "gadgets", "innovation"],
            },
            {
                "caption": "Sunday football vibes 🏈 Go Chiefs!",
                "hashtags": ["nfl", "sports", "football", "chiefskingdom"],
            },
        ]

        return mock_posts


# Global instance
instagram_analyzer = InstagramAnalyzer()
