# 📋 Quick Reference Guide

## 🚀 Getting Started in 5 Minutes

### Local Testing

```bash
# 1. Setup
./setup.sh

# 2. Edit .env (add your ANGEL_API_KEY)
nano .env

# 3. Start Redis
docker run -d -p 6379:6379 redis

# 4. Run backend
source venv/bin/activate
uvicorn app.main:app --reload

# 5. Test
open http://localhost:8000/docs
```

---

### Deploy to Render.com

```bash
# 1. Push to GitHub
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR_USERNAME/fo-backend.git
git push -u origin main

# 2. On Render.com:
# - New + → Blueprint
# - Connect repo
# - Apply
# - Add ANGEL_API_KEY in Environment

# 3. Done! Get your URL:
# https://your-app.onrender.com
```

---

## 🔗 API Endpoints

### Health Check
```
GET https://your-app.onrender.com/health
```

### Login
```bash
POST https://your-app.onrender.com/api/auth/login

{
  "api_key": "your_key",
  "client_code": "your_code",
  "password": "your_password",
  "totp_token": "your_totp_secret"
}
```

### WebSocket (Real-time)
```javascript
const ws = new WebSocket('wss://your-app.onrender.com/ws/NIFTY/client123');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(data); // Live option chain
};
```

---

## 🔧 Environment Variables

```env
ANGEL_API_KEY=your_api_key          # Required: Get from Angel One
SECRET_KEY=auto-generated           # Auto: Render generates
REDIS_URL=redis://...               # Auto: From Render Redis
RISK_FREE_RATE=0.065               # Optional: Default 6.5%
```

---

## 📊 Data Structure

### WebSocket Message Format

```json
{
  "type": "update",
  "data": {
    "timestamp": "2026-01-28T12:00:00",
    "symbol": "NIFTY",
    "spot_price": 23456.78,
    "expiry": "2026-02-27",
    "option_chain": [
      {
        "strike": 23500,
        "option_type": "CE",
        "ltp": 245.50,
        "oi": 45678,
        "oi_change": 2340,
        "volume": 12345,
        "iv": 15.23,
        "delta": 0.5234,
        "gamma": 0.000234,
        "theta": -25.67,
        "vega": 18.45
      }
    ],
    "pcr_oi": 1.23,
    "pcr_volume": 1.15,
    "max_pain": 23500,
    "total_call_oi": 1234567,
    "total_put_oi": 1523456,
    "net_gex": 12345678.90,
    "call_gex": 8234567.89,
    "put_gex": 4111111.01
  }
}
```

---

## 🎨 Frontend Integration (Lovable.ai)

### Environment Variables

```env
VITE_API_URL=https://your-app.onrender.com
VITE_WS_URL=wss://your-app.onrender.com
```

### WebSocket Hook

```javascript
import { useWebSocket } from './hooks/useWebSocket';

function Dashboard() {
  const { isConnected, data } = useWebSocket('NIFTY', clientCode);
  
  return (
    <div>
      Status: {isConnected ? 'Live' : 'Disconnected'}
      Spot: {data?.spot_price}
      PCR: {data?.pcr_oi}
    </div>
  );
}
```

---

## 🐛 Common Issues & Fixes

### Issue: Health check failing
```bash
# Wait 2-3 minutes for Redis to start
# Then check:
curl https://your-app.onrender.com/health
```

### Issue: WebSocket closes
```python
# Update CORS in app/main.py:
allow_origins=["https://your-lovable-app.lovable.app"]
```

### Issue: Spinning down (free tier)
```
# Normal behavior - first request takes 30s
# Upgrade to Starter ($7/mo) for always-on
```

---

## 📚 File Structure

```
fo-backend/
├── app/
│   ├── __init__.py          # Package init
│   └── main.py              # FastAPI app (mock data)
├── requirements.txt         # Python dependencies
├── render.yaml             # Render deployment config
├── .env.example            # Environment template
├── .gitignore              # Git ignore rules
├── README.md               # Full documentation
├── DEPLOYMENT.md           # Deployment guide
├── QUICKREF.md             # This file
└── setup.sh                # Local setup script
```

---

## 🎯 Next Steps

### Current: Mock Data ✅
- Login works (mock)
- WebSocket streams (mock data)
- All calculations working
- Perfect for testing

### Upgrade: Real Angel Data
- Replace mock auth with Angel API
- Add real WebSocket handler
- Compute live IV/Greeks
- See Part 1 & 2 for implementation

---

## 💡 Tips

1. **Test locally first** before deploying
2. **Check health** endpoint after deploy
3. **Monitor logs** in Render dashboard
4. **Use mock data** while building frontend
5. **Upgrade to real data** when frontend complete

---

## 📞 Support Resources

- **Render Docs:** https://render.com/docs
- **FastAPI Docs:** https://fastapi.tiangolo.com
- **Angel API:** https://smartapi.angelbroking.com
- **WebSocket Guide:** https://developer.mozilla.org/en-US/docs/Web/API/WebSocket

---

## ✅ Checklist

**Local Development:**
- [ ] Python 3.10+ installed
- [ ] Virtual environment created
- [ ] Dependencies installed
- [ ] .env configured
- [ ] Redis running
- [ ] Backend running on :8000
- [ ] API docs accessible

**Deployment:**
- [ ] Code on GitHub
- [ ] Render account created
- [ ] Blueprint deployed
- [ ] Environment variables set
- [ ] Health check passing
- [ ] URL copied

**Integration:**
- [ ] Frontend env vars updated
- [ ] WebSocket hook added
- [ ] Login form created
- [ ] Live data flowing
- [ ] End-to-end tested

---

**That's it! You're ready to build your F&O Dashboard! 🎉**
