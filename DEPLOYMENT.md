# 🚀 Render.com Deployment Guide

## Step-by-Step Instructions for Deploying Your F&O Dashboard Backend

---

## ✅ Prerequisites

Before you start:
- [ ] GitHub account
- [ ] Render.com account (free signup)
- [ ] Angel One API key (from smartapi.angelbroking.com)

---

## 📤 STEP 1: Push Code to GitHub

### Option A: Using GitHub Desktop (Easiest)

1. Download and install [GitHub Desktop](https://desktop.github.com/)
2. Open GitHub Desktop
3. Click **File** → **Add Local Repository**
4. Select your `fo-backend` folder
5. Click **Publish repository**
6. Uncheck "Keep this code private" (or keep checked, either works)
7. Click **Publish repository**

### Option B: Using Command Line

```bash
# Navigate to your project folder
cd fo-backend

# Initialize git
git init

# Add all files
git add .

# Commit
git commit -m "Initial commit - F&O Dashboard Backend"

# Create GitHub repo at https://github.com/new
# Then connect and push:
git remote add origin https://github.com/YOUR_USERNAME/fo-backend.git
git branch -M main
git push -u origin main
```

**✅ Checkpoint:** Your code should now be visible on GitHub

---

## 🌐 STEP 2: Deploy on Render.com

### 2.1 Sign Up / Login

1. Go to [render.com](https://render.com)
2. Click **Get Started**
3. Sign up with GitHub (recommended) or email

### 2.2 Connect GitHub Repository

1. Click **Dashboard**
2. Click **New +** (top right)
3. Select **Blueprint**
4. Click **Connect a repository**
5. Find and select your `fo-backend` repository
6. Click **Connect**

### 2.3 Configure Blueprint

Render will automatically detect `render.yaml` and show:

✅ **Web Service:** `fo-dashboard-backend`  
✅ **Redis:** `fo-redis`

Click **Apply**

### 2.4 Set Environment Variables

Before deployment, you need to add your Angel API key:

1. After clicking Apply, you'll see the services being created
2. Click on **fo-dashboard-backend** (the web service)
3. Go to **Environment** tab (left sidebar)
4. You'll see these auto-populated:
   - `PYTHON_VERSION` = 3.11.0
   - `SECRET_KEY` = (auto-generated)
   - `REDIS_URL` = (auto-connected to Redis)

5. **Add your Angel API key:**
   - Click **Add Environment Variable**
   - Key: `ANGEL_API_KEY`
   - Value: `your_actual_angel_api_key`
   - Click **Save**

### 2.5 Deploy!

1. Render will automatically start building
2. Watch the **Logs** tab for progress
3. Build takes ~3-5 minutes

**Build steps you'll see:**
```
==> Downloading cache...
==> Installing dependencies
==> Building...
==> Uploading build...
==> Starting service
==> Deploy successful!
```

---

## ✅ STEP 3: Verify Deployment

### 3.1 Get Your Backend URL

After deployment completes:

1. Go to your web service dashboard
2. Find the URL at the top (e.g., `fo-dashboard-backend.onrender.com`)
3. Copy this URL - you'll need it for Lovable.ai

### 3.2 Test Endpoints

**Health Check:**
```
https://your-app.onrender.com/health
```

Expected response:
```json
{
  "status": "healthy",
  "redis": "connected",
  "active_connections": 0,
  "timestamp": "2026-01-28T..."
}
```

**API Docs:**
```
https://your-app.onrender.com/docs
```

You should see the FastAPI Swagger interface.

**Test WebSocket (in browser console):**
```javascript
const ws = new WebSocket('wss://your-app.onrender.com/ws/NIFTY/test');
ws.onmessage = (e) => console.log(JSON.parse(e.data));
```

---

## 🔗 STEP 4: Connect to Lovable.ai

### 4.1 Update Frontend Environment

In Lovable.ai, update environment variables:

```env
VITE_API_URL=https://your-app.onrender.com
VITE_WS_URL=wss://your-app.onrender.com
```

### 4.2 Tell Lovable to Integrate

Give Lovable.ai this message:

```
My backend is deployed at: https://your-app.onrender.com

Please implement:
1. API service to connect to my backend
2. WebSocket hook for real-time data
3. Login form for Angel One credentials
4. Connect live data to the dashboard

Endpoints:
- POST /api/auth/login - Login with Angel credentials
- GET /api/auth/session/{client_code} - Check session
- WS /ws/{symbol}/{client_code} - Real-time option chain

WebSocket message format:
{
  "type": "update",
  "data": {
    "timestamp": "...",
    "symbol": "NIFTY",
    "spot_price": 23456.78,
    "option_chain": [...],
    "pcr_oi": 1.23,
    "max_pain": 23500,
    ...
  }
}
```

---

## 🎯 STEP 5: Final Testing

### Test the Complete Flow:

1. **Frontend Login:**
   - Open your Lovable.ai app
   - Enter Angel credentials
   - Should see "Login successful"

2. **WebSocket Connection:**
   - Should see "Live" indicator turn green
   - Data should start flowing

3. **Dashboard Updates:**
   - Option chain should update every second
   - PCR, Max Pain, GEX should display
   - Spot price should be live

---

## 🐛 Troubleshooting

### Issue: "Service not starting"

**Check logs:**
1. Go to Render dashboard
2. Click your web service
3. Click **Logs** tab
4. Look for error messages

**Common causes:**
- Missing dependencies in requirements.txt
- Python version mismatch
- Redis connection timeout

**Fix:**
- Redeploy after fixing
- Check environment variables

---

### Issue: "Health check failing"

**Symptoms:**
- Service shows "Unhealthy"
- Red dot next to service name

**Causes:**
- Redis not fully started (takes 2-3 min)
- Port configuration issue

**Fix:**
1. Wait 3-5 minutes
2. Check `/health` endpoint manually
3. Redeploy if still failing

---

### Issue: "WebSocket closes immediately"

**Check:**
1. CORS configuration in `main.py`
2. WebSocket URL uses `wss://` not `ws://`
3. Client code is valid

**Fix:**
Update CORS in `app/main.py`:
```python
allow_origins=["https://your-lovable-app.lovable.app"]
```

---

### Issue: "Free tier spinning down"

**Symptoms:**
- First request takes 30+ seconds
- Service "sleeping" after inactivity

**This is normal on free tier!**

**Solutions:**
1. Wait 30 seconds for wake-up
2. Upgrade to Starter ($7/mo) for always-on
3. Use a ping service to keep alive

---

## 📊 Monitoring Your Service

### Render Dashboard

**Metrics to watch:**
- CPU usage
- Memory usage
- Request count
- Active connections

**Set up alerts:**
1. Go to service settings
2. Click **Notifications**
3. Add email/Slack notifications

---

## 🆙 Next Steps

### Current Status: ✅ Mock Data

Your backend is running with **mock data** for testing.

### Upgrade to Real Angel Data

When ready, update `app/main.py`:

1. Replace mock login with real Angel API
2. Add Angel WebSocket handler
3. Compute real IV/Greeks
4. Test with market hours

See full implementation in **Part 1 & 2** of the plan.

---

## 💰 Cost Breakdown

### Free Tier (Current)

- ✅ Web service: FREE
- ✅ Redis: FREE
- ⏱️ Spins down after 15 min
- 💾 512 MB RAM

**Good for:** Testing, development

### Starter Tier ($7/month)

- ✅ Always-on
- ✅ Faster
- ✅ More reliable

**Good for:** Production, live trading

---

## 📝 Deployment Checklist

- [ ] Code pushed to GitHub
- [ ] Render account created
- [ ] Blueprint deployed
- [ ] Redis service running
- [ ] Environment variables set
- [ ] Health check passing
- [ ] API docs accessible
- [ ] WebSocket tested
- [ ] Frontend connected
- [ ] End-to-end tested

---

## 🎉 You're Done!

Your F&O Dashboard backend is now live and ready to stream data!

**Your URLs:**
- Backend: `https://your-app.onrender.com`
- Docs: `https://your-app.onrender.com/docs`
- Health: `https://your-app.onrender.com/health`

**Questions?** Check the troubleshooting section or README.md

---

**Happy Trading! 📈**
