# 🔮 PredictionZ

> AI-powered prediction market analysis with brutalist Gen Z design

[![Live Demo](https://img.shields.io/badge/demo-live-success)](https://predictionz.vercel.app)
[![API](https://img.shields.io/badge/api-docs-blue)](https://api.predictionz.com/docs)

## 🎯 What is PredictionZ?

PredictionZ combines **Claude AI** with **Polymarket** to give Gen Z traders instant, intelligent market analysis with a bold neo-brutalist interface.

**TL;DR:** AI tells you what to bet on, with odds that slap fr fr 💀

---

## ✨ Features

### 🤖 AI-Powered Analysis
- **Claude Sonnet 4.5** analyzes every market
- Confidence scores (0-100%)
- Risk levels (💀 to 💀💀💀💀💀)
- Gen Z language: "no cap", "locked in", "fr fr"

### 📊 Real-Time Market Data
- Live odds from Polymarket
- Volume & liquidity metrics
- Order book visualization
- Recent trades feed

### 🎨 Neo-Brutalist Design
- Bold black borders
- Stark contrast (black/white)
- Neon accents (pink, lime, yellow)
- Zero rounded corners
- Thick shadows
- Geometric layouts

### 💰 Smart Trading
- One-click bet placement
- WalletConnect integration
- Portfolio tracking
- P&L visualization

---

## 🛠️ Tech Stack

### Frontend (Lovable + Vercel)
- **React 18** + TypeScript
- **Vite** - Lightning fast builds
- **Tailwind CSS** - Brutalist styling
- **Supabase** - Backend/DB
- **Framer Motion** - Animations
- **Web3Modal** - Wallet connection

### Backend (FastAPI + Railway)
- **FastAPI** - High-performance API
- **Claude API** - AI analysis (Anthropic)
- **Polymarket CLOB** - Market data
- **Python 3.11+**

### Blockchain
- **Polygon** - Polymarket network
- **USDC** - Betting currency
- **ethers.js** - Web3 interactions

---

## 🚀 Quick Start

### Prerequisites
```bash
- Node.js 18+
- Python 3.11+
- Claude API key (Anthropic)
- Supabase account
```

### Backend Setup

1. Clone repository:
```bash
git clone https://github.com/anthonysurfermx/PredictionZ.git
cd PredictionZ
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create `.env`:
```env
ANTHROPIC_API_KEY=your_claude_api_key
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
```

4. Run server:
```bash
python app.py
```

API will be available at `http://localhost:8000`

### Frontend Setup

Use **Lovable** to generate the frontend:
1. Go to [lovable.dev](https://lovable.dev)
2. Use the prompt from this README
3. Connect to Supabase
4. Deploy to Vercel

---

## 📡 API Endpoints

### Markets
```
GET  /api/markets              - List active markets
GET  /api/markets/:id          - Market details
GET  /api/search?q=trump       - Search markets
```

### AI Analysis
```
POST /api/analyze              - Get AI analysis
GET  /api/markets/:id/analysis - Market analysis
```

### Trading Data
```
GET /api/orderbook/:token_id   - Order book
GET /api/trades/:id            - Recent trades
```

Full API docs: `http://localhost:8000/docs`

---

## 🎨 Design System

### Colors
```css
--black: #000000;
--white: #FFFFFF;
--neon-pink: #FF006E;
--lime: #39FF14;
--yellow: #FFD700;
```

### Typography
- Headers: **Inter Black**
- Body: **Inter Regular**
- Mono: **JetBrains Mono**

### Spacing
- Borders: 4-8px solid
- Shadows: 8px offset
- Padding: 16px/24px/32px

---

## 🤖 AI Analysis Example

```json
{
  "confidence": 0.78,
  "prediction": "YES",
  "reasoning": [
    "Trump leading in swing state polls by 5+ points",
    "Betting markets showing strong momentum",
    "Historical precedent favors incumbent advantage"
  ],
  "sentiment": "bullish",
  "risk_level": 3,
  "recommendation": "BUY",
  "gen_z_take": "Trump's odds looking solid rn, no cap 📈"
}
```

---

## 📱 Screenshots

[Add screenshots here after deploying]

---

## 🎯 Roadmap

### Phase 1 (MVP) ✅
- [x] Polymarket integration
- [x] Claude AI analysis
- [x] Brutalist UI
- [x] Wallet connection

### Phase 2
- [ ] Portfolio tracking
- [ ] Price alerts
- [ ] Social sentiment analysis
- [ ] Mobile app (iOS/Android)

### Phase 3
- [ ] AI trading bot
- [ ] Copy trading
- [ ] DAO governance
- [ ] Token launch

---

## 🤝 Contributing

We welcome PRs! See [CONTRIBUTING.md](CONTRIBUTING.md)

```bash
git checkout -b feature/amazing-feature
git commit -m 'Add amazing feature'
git push origin feature/amazing-feature
```

---

## 📄 License

MIT License - see [LICENSE](LICENSE)

---

## 👥 Team

- **[@anthonysurfermx](https://github.com/anthonysurfermx)** - Creator

---

## 🙏 Acknowledgments

- **Anthropic** - Claude AI API
- **Polymarket** - Prediction market infrastructure
- **Lovable** - Frontend generation
- **Supabase** - Backend infrastructure

---

## 📞 Contact

- 🌐 Website: [predictionz.vercel.app](https://predictionz.vercel.app)
- 📧 Email: contact@predictionz.com
- 🐦 Twitter: [@PredictionZ](https://twitter.com/PredictionZ)

---

<div align="center">

**Built different, no cap** 💀🔥

[⭐ Star](https://github.com/anthonysurfermx/PredictionZ) | [🐛 Report Bug](https://github.com/anthonysurfermx/PredictionZ/issues) | [✨ Request Feature](https://github.com/anthonysurfermx/PredictionZ/issues)

</div>
