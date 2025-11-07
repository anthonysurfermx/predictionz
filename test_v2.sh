#!/bin/bash

echo "🧪 Testing V2 Recommendation Engine"
echo "=================================="
echo ""

# Test recommendations
echo "1. Testing /api/recommend with V2..."
response=$(curl -s -X POST http://localhost:8000/api/recommend \
  -H "Content-Type: application/json" \
  -d '{"preferences": {"categories": ["crypto", "tech"], "risk_tolerance": "medium"}, "limit": 3}')

echo "$response" | python3 -c "
import sys, json
data = json.load(sys.stdin)

print(f\"✅ Success: {data['success']}\")
print(f\"📊 Count: {data['count']}\")
print(f\"\")
print(f\"Top Recommendations:\")

for i, market in enumerate(data['markets'][:3], 1):
    print(f\"\n{i}. {market['title']}\")
    print(f\"   Score: {market.get('recommendation_score', 'N/A')}\")

    if 'score_breakdown' in market:
        print(f\"   Breakdown:\")
        for k, v in market['score_breakdown'].items():
            print(f\"     {k}: {v:.1f}\")
"

echo ""
echo "=================================="
echo "2. Testing viral context detection..."

response2=$(curl -s http://localhost:8000/api/trending?limit=3)

echo "$response2" | python3 -c "
import sys, json
data = json.load(sys.stdin)

print(f\"✅ Success: {data['success']}\")
print(f\"🔥 Trending Markets:\")

for i, market in enumerate(data['markets'][:3], 1):
    print(f\"\n{i}. {market['title']}\")
    print(f\"   Volume: \${market.get('volume', 0):,.0f}\")
"

echo ""
echo "✅ V2 Testing Complete!"
