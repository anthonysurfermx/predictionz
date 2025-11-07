#!/bin/bash

echo "🧪 Testing Complete Market Flow"
echo "================================"
echo ""

# Step 1: Get markets list
echo "1️⃣  Fetching markets list..."
markets_response=$(curl -s "http://localhost:8000/api/markets?limit=3")
market_id=$(echo "$markets_response" | python3 -c "
import sys, json
data = json.load(sys.stdin)
if data.get('success') and data.get('markets'):
    market = data['markets'][0]
    print(market['id'])
" 2>/dev/null)

if [ -z "$market_id" ]; then
    echo "❌ Failed to get markets"
    exit 1
fi

echo "✅ Got market ID: ${market_id:0:20}..."
echo ""

# Step 2: Get market detail
echo "2️⃣  Fetching market detail..."
detail_response=$(curl -s "http://localhost:8000/api/markets/$market_id")
echo "$detail_response" | python3 -c "
import sys, json
data = json.load(sys.stdin)
if data.get('success'):
    market = data['market']
    print(f'✅ Market Detail:')
    print(f'   Title: {market[\"title\"]}')
    print(f'   Category: {market[\"category\"]}')
    print(f'   Volume: \${market[\"volume\"]:,.0f}')
    print(f'   Odds YES: {market[\"odds_yes\"] * 100:.1f}%')
    print(f'   Odds NO: {market[\"odds_no\"] * 100:.1f}%')
else:
    print('❌ Failed to get market detail')
    print('Error:', data.get('detail', 'Unknown'))
    exit(1)
" || exit 1

echo ""
echo "3️⃣  Frontend Integration:"
echo "   You can now click on markets at:"
echo "   http://localhost:8081"
echo "   And view details at:"
echo "   http://localhost:8081/market/$market_id"
echo ""
echo "✅ All tests passed!"
