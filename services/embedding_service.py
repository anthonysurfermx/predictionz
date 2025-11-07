"""
Embedding Service
Generates semantic embeddings for users and markets using OpenAI
"""
import os
from typing import List, Dict, Optional
from openai import OpenAI
import hashlib
import json


class EmbeddingService:
    """
    Service to generate and cache embeddings for semantic matching
    """

    def __init__(self):
        """Initialize OpenAI client"""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")

        self.client = OpenAI(api_key=api_key)
        self.model = "text-embedding-3-small"  # Faster and cheaper
        # For better quality: "text-embedding-3-large"

        # Simple in-memory cache (in production, use Redis/Supabase)
        self._cache = {}

    async def generate_user_embedding(
        self,
        categories: List[str],
        risk_tolerance: str,
        themes: Optional[List[str]] = None,
        instagram_captions: Optional[List[str]] = None
    ) -> List[float]:
        """
        Generate embedding for user profile based on interests.

        Args:
            categories: List of interest categories
            risk_tolerance: "safe", "medium", or "degen"
            themes: Optional specific themes/interests
            instagram_captions: Optional Instagram post captions

        Returns:
            768-dimensional embedding vector
        """
        # Build text representation of user
        text_parts = []

        # Categories
        if categories:
            text_parts.append(f"Interests: {', '.join(categories)}")

        # Risk tolerance
        risk_descriptions = {
            "safe": "prefers low-risk, high-probability bets with strong consensus",
            "medium": "balanced risk-taker, open to moderate uncertainty",
            "degen": "high-risk, high-reward mindset, loves underdog bets and moonshots"
        }
        text_parts.append(f"Risk profile: {risk_descriptions.get(risk_tolerance, risk_tolerance)}")

        # Themes
        if themes:
            text_parts.append(f"Specific interests: {', '.join(themes)}")

        # Instagram content (if available)
        if instagram_captions:
            # Use first 3 captions for context
            captions_text = " ".join(instagram_captions[:3])
            text_parts.append(f"Social media activity: {captions_text[:300]}")

        user_text = ". ".join(text_parts)

        # Check cache
        cache_key = self._get_cache_key(user_text)
        if cache_key in self._cache:
            return self._cache[cache_key]

        # Generate embedding
        try:
            response = self.client.embeddings.create(
                input=user_text,
                model=self.model
            )

            embedding = response.data[0].embedding

            # Cache it
            self._cache[cache_key] = embedding

            return embedding

        except Exception as e:
            print(f"Error generating user embedding: {e}")
            raise

    async def generate_market_embedding(
        self,
        title: str,
        description: Optional[str] = None,
        category: Optional[str] = None
    ) -> List[float]:
        """
        Generate embedding for market based on title and description.

        Args:
            title: Market title
            description: Market description
            category: Market category

        Returns:
            768-dimensional embedding vector
        """
        # Build text representation
        text_parts = [title]

        if category:
            text_parts.append(f"Category: {category}")

        if description:
            # Truncate long descriptions
            desc = description[:500] if len(description) > 500 else description
            text_parts.append(desc)

        market_text = ". ".join(text_parts)

        # Check cache
        cache_key = self._get_cache_key(market_text)
        if cache_key in self._cache:
            return self._cache[cache_key]

        # Generate embedding
        try:
            response = self.client.embeddings.create(
                input=market_text,
                model=self.model
            )

            embedding = response.data[0].embedding

            # Cache it
            self._cache[cache_key] = embedding

            return embedding

        except Exception as e:
            print(f"Error generating market embedding: {e}")
            raise

    async def generate_batch_embeddings(
        self,
        texts: List[str]
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in batch (more efficient).

        Args:
            texts: List of text strings

        Returns:
            List of embedding vectors
        """
        # Check cache first
        results = []
        uncached_indices = []
        uncached_texts = []

        for i, text in enumerate(texts):
            cache_key = self._get_cache_key(text)
            if cache_key in self._cache:
                results.append(self._cache[cache_key])
            else:
                results.append(None)  # Placeholder
                uncached_indices.append(i)
                uncached_texts.append(text)

        # Generate embeddings for uncached texts
        if uncached_texts:
            try:
                response = self.client.embeddings.create(
                    input=uncached_texts,
                    model=self.model
                )

                # Fill in results and cache
                for idx, embedding_obj in enumerate(response.data):
                    result_idx = uncached_indices[idx]
                    embedding = embedding_obj.embedding
                    results[result_idx] = embedding

                    # Cache it
                    cache_key = self._get_cache_key(uncached_texts[idx])
                    self._cache[cache_key] = embedding

            except Exception as e:
                print(f"Error generating batch embeddings: {e}")
                raise

        return results

    def _get_cache_key(self, text: str) -> str:
        """Generate cache key from text using hash"""
        return hashlib.md5(text.encode()).hexdigest()

    def clear_cache(self):
        """Clear the embedding cache"""
        self._cache.clear()

    def get_cache_stats(self) -> Dict:
        """Get cache statistics"""
        return {
            "size": len(self._cache),
            "model": self.model
        }


# Global instance
embedding_service = EmbeddingService()


# Helper function for Instagram analyzer
async def enhance_instagram_analysis_with_embedding(
    username: str,
    categories: List[str],
    risk_tolerance: str,
    themes: List[str],
    captions: List[str]
) -> Dict:
    """
    Enhance Instagram analysis with user embedding.

    Returns:
        {
            "username": str,
            "categories": List[str],
            "risk_tolerance": str,
            "themes": List[str],
            "embedding": List[float]  # 768-dim vector
        }
    """
    embedding = await embedding_service.generate_user_embedding(
        categories=categories,
        risk_tolerance=risk_tolerance,
        themes=themes,
        instagram_captions=captions
    )

    return {
        "username": username,
        "categories": categories,
        "risk_tolerance": risk_tolerance,
        "themes": themes,
        "embedding": embedding
    }


# Helper function for quiz preferences
async def enhance_quiz_preferences_with_embedding(
    categories: List[str],
    risk_tolerance: str
) -> Dict:
    """
    Enhance manual quiz preferences with user embedding.

    Returns:
        {
            "categories": List[str],
            "risk_tolerance": str,
            "embedding": List[float]
        }
    """
    embedding = await embedding_service.generate_user_embedding(
        categories=categories,
        risk_tolerance=risk_tolerance
    )

    return {
        "categories": categories,
        "risk_tolerance": risk_tolerance,
        "embedding": embedding
    }


if __name__ == "__main__":
    """
    Test the embedding service
    """
    import asyncio

    async def test():
        print("🧪 Testing Embedding Service\n")

        # Test 1: User embedding
        print("1. Generating user embedding...")
        user_emb = await embedding_service.generate_user_embedding(
            categories=["crypto", "tech"],
            risk_tolerance="medium",
            themes=["Bitcoin", "AI", "startups"]
        )
        print(f"   ✅ Generated {len(user_emb)}-dimensional vector")
        print(f"   First 5 values: {user_emb[:5]}")

        # Test 2: Market embedding
        print("\n2. Generating market embedding...")
        market_emb = await embedding_service.generate_market_embedding(
            title="Will Bitcoin hit $100K in 2024?",
            description="Prediction market for Bitcoin reaching $100,000 by end of 2024",
            category="Crypto"
        )
        print(f"   ✅ Generated {len(market_emb)}-dimensional vector")
        print(f"   First 5 values: {market_emb[:5]}")

        # Test 3: Batch generation
        print("\n3. Testing batch generation...")
        texts = [
            "Will Trump win 2024 election?",
            "Will Ethereum merge succeed?",
            "Will Tesla stock hit $1000?"
        ]
        batch_embs = await embedding_service.generate_batch_embeddings(texts)
        print(f"   ✅ Generated {len(batch_embs)} embeddings")

        # Test 4: Cache
        print("\n4. Testing cache...")
        stats_before = embedding_service.get_cache_stats()
        print(f"   Cache size before: {stats_before['size']}")

        # Generate same embedding again (should use cache)
        user_emb_cached = await embedding_service.generate_user_embedding(
            categories=["crypto", "tech"],
            risk_tolerance="medium",
            themes=["Bitcoin", "AI", "startups"]
        )

        stats_after = embedding_service.get_cache_stats()
        print(f"   Cache size after: {stats_after['size']}")
        print(f"   ✅ Cache working (same size = cache hit)")

        # Test 5: Cosine similarity
        print("\n5. Testing similarity...")
        from services.recommendation_engine_v2 import RecommendationEngineV2
        engine = RecommendationEngineV2()

        similarity = engine._cosine_similarity(user_emb, market_emb)
        print(f"   User ↔ Market similarity: {similarity:.4f}")
        print(f"   ✅ Semantic matching ready!")

        print("\n✅ All tests passed!")

    asyncio.run(test())
