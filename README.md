# 🚀 F&O Dashboard Backend

FastAPI backend for real-time F&O option chain analytics with Angel One SmartAPI integration.

## 📋 Features

- ✅ Angel One authentication (JWT + TOTP)
- ✅ Real-time WebSocket streaming
- ✅ Option chain calculations (IV, Greeks, GEX, PCR, Max Pain)
- ✅ Redis caching
- ✅ Mock data for testing
- ✅ Production-ready with Render.com deployment

## 🛠️ Tech Stack

- **FastAPI** - Modern Python web framework
- **WebSockets** - Real-time data streaming
- **Redis** - Caching layer
- **Angel One SmartAPI** - Market data
- **py_vollib** - Options pricing calculations

---

## 🚀 Quick Start (Local Development)

### 1. Prerequisites

- Python 3.10+
- Redis (via Docker or local install)
- Angel One API credentials

### 2. Installation

```bash
# Clone or create project folder
mkdir fo-dashboard-backend
cd fo-dashboard-backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration

Create `.env` file:

```env
ANGEL_API_KEY=your_angel_api_key
SECRET_KEY=your-secret-key-here
REDIS_URL=redis://localhost:6379
RISK_FREE_RATE=0.065
```

### 4. Run Redis (Docker)

```bash
docker run -d -p 6379:6379 redis:7-alpine
```

### 5. Run Backend

```bash
# Development mode with auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend will be available at:
- API: http://localhost:8000
- Docs: http://localhost:8000/docs
- Health: http://localhost:8000/health

---

## 🌐 Deploy to Render.com (FREE)

### Step 1: Push to GitHub

```bash
# Initialize git
git init
git add .
git commit -m "Initial commit"

# Create GitHub repo and push
git remote add origin https://github.com/YOUR_USERNAME/fo-backend.git
git branch -M main
git push -u origin main
```

### Step 2: Deploy on Render.com

1. **Go to** [render.com](https://render.com) and sign up

2. **Click** "New +" → "Blueprint"

3. **Connect** your GitHub repository

4. **Render will auto-detect** `render.yaml` and create:
   - Web Service (FastAPI)
   - Redis instance

5. **Set Environment Variables**:
   - Go to your web service
   - Click "Environment"
   - Add: `ANGEL_API_KEY` = `your_key`
   - (Other vars auto-populate from render.yaml)

6. **Deploy** - Click "Manual Deploy" → "Deploy latest commit"

### Step 3: Get Your Backend URL

After deployment completes:
```
https://fo-dashboard-backend.onrender.com
```

### Step 4: Test Deployment

```bash
# Health check
curl https://fo-dashboard-backend.onrender.com/health

# API docs
open https://fo-dashboard-backend.onrender.com/docs
```

---

## 🔗 Connect to Lovable.ai Frontend

### Update Frontend Environment Variables

In Lovable.ai, set:

```env
VITE_API_URL=https://fo-dashboard-backend.onrender.com
VITE_WS_URL=wss://fo-dashboard-backend.onrender.com
```

### Test WebSocket Connection

```javascript
const ws = new WebSocket('wss://fo-dashboard-backend.onrender.com/ws/NIFTY/test_user');

ws.onopen = () => console.log('Connected!');
ws.onmessage = (event) => console.log('Data:', JSON.parse(event.data));
```

---

## 📡 API Endpoints

### Authentication

**POST** `/api/auth/login`
```json
{
  "api_key": "your_api_key",
  "client_code": "your_client_code",
  "password": "your_password",
  "totp_token": "your_totp_secret"
}
```

**GET** `/api/auth/session/{client_code}`

### Data

**GET** `/api/spot/{symbol}` - Get spot price

**GET** `/api/option-chain/{symbol}` - Get option chain (REST)

**WebSocket** `/ws/{symbol}/{client_code}` - Real-time stream

### Health

**GET** `/health` - Health check

**GET** `/` - Root info

---

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ANGEL_API_KEY` | Angel One API key | Required |
| `SECRET_KEY` | JWT secret | Auto-generated |
| `REDIS_URL` | Redis connection URL | Auto from Render |
| `RISK_FREE_RATE` | Risk-free rate for options | 0.065 (6.5%) |

### Render.com Settings

Edit `render.yaml` to customize:
- Region (oregon, frankfurt, singapore)
- Plan (free, starter, standard)
- Environment variables
- Health check path

---

## 🐛 Troubleshooting

### Issue: "Redis connection failed"

**Solution**: Render's Redis takes 2-3 minutes to start. Wait and redeploy.

### Issue: "WebSocket closes immediately"

**Solution**: Check CORS settings in `main.py`. Add your Lovable.ai domain to `allow_origins`.

### Issue: "Health check failing"

**Solution**: Render's free tier spins down after inactivity. First request takes ~30 seconds.

### Issue: "Angel API login fails"

**Solution**: 
1. Verify API key is correct
2. Check TOTP secret (not the 6-digit code)
3. Ensure Angel account has API access enabled

---

## 📊 Mock Data vs Real Data

### Current Setup (Mock Data)

The backend is configured with **mock data generation** for testing without Angel API:

- ✅ Realistic option chain
- ✅ Random OI/Volume/Greeks
- ✅ PCR, Max Pain, GEX calculations
- ✅ 1-second updates

### Switch to Real Angel Data

Replace in `app/main.py`:

```python
# In login endpoint:
from smartapi import SmartConnect
smart_api = SmartConnect(api_key=request.api_key)
data = smart_api.generateSession(...)

# In WebSocket endpoint:
from app.services.angel_websocket import AngelWebSocketHandler
# Use real Angel WebSocket instead of MockDataGenerator
```

---

## 🔐 Security Notes

### Production Checklist

- [ ] Replace mock auth with real Angel API
- [ ] Set strong `SECRET_KEY`
- [ ] Configure CORS for specific domains only
- [ ] Enable HTTPS (automatic on Render)
- [ ] Add rate limiting
- [ ] Set up monitoring/alerts
- [ ] Rotate API keys regularly

### CORS Configuration

In production, update `main.py`:

```python
ALLOWED_ORIGINS = [
    "https://your-lovable-app.lovable.app",
    "https://your-custom-domain.com"
]
```

---

## 📈 Monitoring

### Render Dashboard

- View logs: Dashboard → Logs
- Monitor metrics: Dashboard → Metrics
- Check health: https://your-app.onrender.com/health

### Key Metrics

- Active WebSocket connections
- Redis connection status
- Request latency
- Error rates

---

## 🆙 Upgrading from Free Tier

Render.com free tier limitations:
- ⏱️ Spins down after 15 min inactivity
- 💾 512 MB RAM
- ⚡ Shared CPU

### Upgrade to Starter ($7/month):
- ✅ Always-on
- ✅ 512 MB RAM (dedicated)
- ✅ Faster startup
- ✅ Better for production

---

## 📝 Development Workflow

### Local Development

```bash
# 1. Start Redis
docker run -d -p 6379:6379 redis

# 2. Run backend
uvicorn app.main:app --reload

# 3. Test in browser
open http://localhost:8000/docs
```

### Push to Production

```bash
# Commit changes
git add .
git commit -m "Update feature"
git push

# Render auto-deploys on push
# Check deployment status in dashboard
```

---

## 🤝 Support

### Issues?

1. Check Render logs
2. Verify environment variables
3. Test health endpoint
4. Review CORS settings

### Next Steps

1. ✅ Deploy backend to Render
2. ✅ Get backend URL
3. ✅ Update Lovable.ai environment variables
4. ✅ Connect frontend to backend
5. ✅ Test end-to-end

---

## 📚 Resources

- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [Render Docs](https://render.com/docs)
- [Angel SmartAPI](https://smartapi.angelbroking.com/)
- [WebSocket Guide](https://fastapi.tiangolo.com/advanced/websockets/)

---

## 📄 License

MIT License - Free to use and modify

---

**Ready to deploy?** Follow the Render.com deployment steps above! 🚀
