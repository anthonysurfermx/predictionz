#!/bin/bash

echo "🧪 Testing Instagram Integration with Date Filtering"
echo "====================================================="
echo ""

response=$(curl -s -X POST http://localhost:8000/api/analyze-instagram \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser"}')

echo "$response" | python3 -c "
import sys, json

data = json.load(sys.stdin)

if data.get('success'):
    print(f\"✅ Success: {data['success']}\")
    print(f\"👤 Username: {data.get('username')}\")
    print(f\"📊 Markets found: {len(data.get('markets', []))}\")
    print(f\"\")
    print(f\"Top 5 Markets:\")

    for i, market in enumerate(data.get('markets', [])[:5], 1):
        title = market.get('title', 'N/A')
        end_date = market.get('end_date', 'N/A')
        score = market.get('recommendation_score', 0)

        year = 'N/A'
        if end_date and end_date != 'N/A':
            try:
                year = end_date[:4]
            except:
                pass

        print(f\"{i}. {title[:70]}...\")
        print(f\"   Year: {year} | Score: {score}\")
        print(\"\")
else:
    print(f\"❌ Error: {data}\")
"

echo ""
echo "✅ Test Complete!"
