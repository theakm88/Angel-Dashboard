"""
F&O Dashboard Backend - FastAPI Application
Production-ready version with simplified structure for Render.com
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import Dict, List, Optional
import redis.asyncio as redis
import logging
import json
import asyncio
from datetime import datetime
from pydantic import BaseModel
import os
import random

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
ANGEL_API_KEY = os.getenv("ANGEL_API_KEY", "")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key")
RISK_FREE_RATE = float(os.getenv("RISK_FREE_RATE", "0.065"))

# Global state
app_state = {
    'redis': None,
    'active_connections': {}
}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup
    try:
        app_state['redis'] = await redis.from_url(
            REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            socket_connect_timeout=5
        )
        logger.info("✅ Redis connected")
        await app_state['redis'].ping()
        logger.info("✅ Redis ping successful")
    except Exception as e:
        logger.error(f"❌ Redis connection failed: {e}")
        app_state['redis'] = None
    
    yield
    
    # Shutdown
    if app_state['redis']:
        await app_state['redis'].close()
        logger.info("Redis connection closed")

# Initialize FastAPI
app = FastAPI(
    title="F&O Dashboard API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class LoginRequest(BaseModel):
    api_key: str
    client_code: str
    password: str
    totp_token: str

class LoginResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict] = None

# Mock Data Generator
def generate_mock_option_chain(symbol: str = "NIFTY"):
    """Generate realistic mock option chain data"""
    spot_price = 23456.78
    strikes = [spot_price - 500 + (i * 100) for i in range(15)]
    
    option_chain = []
    
    for strike in strikes:
        # Call option
        ce_oi = random.randint(10000, 100000)
        ce_volume = random.randint(1000, 50000)
        ce_ltp = max(1, abs(spot_price - strike) * random.uniform(0.01, 0.05))
        
        option_chain.append({
            'strike': strike,
            'option_type': 'CE',
            'ltp': round(ce_ltp, 2),
            'oi': ce_oi,
            'oi_change': random.randint(-5000, 5000),
            'volume': ce_volume,
            'iv': round(random.uniform(12, 18), 2),
            'delta': round(random.uniform(0.3, 0.8), 4),
            'gamma': round(random.uniform(0.0001, 0.001), 6),
            'theta': round(random.uniform(-50, -10), 2),
            'vega': round(random.uniform(10, 30), 2),
        })
        
        # Put option
        pe_oi = random.randint(10000, 100000)
        pe_volume = random.randint(1000, 50000)
        pe_ltp = max(1, abs(strike - spot_price) * random.uniform(0.01, 0.05))
        
        option_chain.append({
            'strike': strike,
            'option_type': 'PE',
            'ltp': round(pe_ltp, 2),
            'oi': pe_oi,
            'oi_change': random.randint(-5000, 5000),
            'volume': pe_volume,
            'iv': round(random.uniform(12, 18), 2),
            'delta': round(random.uniform(-0.8, -0.3), 4),
            'gamma': round(random.uniform(0.0001, 0.001), 6),
            'theta': round(random.uniform(-50, -10), 2),
            'vega': round(random.uniform(10, 30), 2),
        })
    
    # Calculate metrics
    total_call_oi = sum(opt['oi'] for opt in option_chain if opt['option_type'] == 'CE')
    total_put_oi = sum(opt['oi'] for opt in option_chain if opt['option_type'] == 'PE')
    pcr_oi = round(total_put_oi / total_call_oi, 2) if total_call_oi > 0 else 0
    max_pain = strikes[len(strikes) // 2]
    net_gex = random.uniform(-100000000, 100000000)
    
    return {
        'timestamp': datetime.now().isoformat(),
        'symbol': symbol,
        'spot_price': spot_price,
        'expiry': '2026-02-27',
        'option_chain': option_chain,
        'pcr_oi': pcr_oi,
        'pcr_volume': round(random.uniform(0.8, 1.5), 2),
        'max_pain': max_pain,
        'total_call_oi': total_call_oi,
        'total_put_oi': total_put_oi,
        'total_call_volume': random.randint(100000, 500000),
        'total_put_volume': random.randint(100000, 500000),
        'net_gex': round(net_gex, 2),
        'call_gex': round(abs(net_gex) * 0.6, 2),
        'put_gex': round(abs(net_gex) * 0.4, 2),
    }

# Endpoints
@app.post("/api/auth/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """Login endpoint (mock)"""
    try:
        if not request.api_key or not request.client_code:
            return LoginResponse(success=False, message="Invalid credentials")
        
        mock_feed_token = f"mock_feed_token_{request.client_code}"
        
        if app_state['redis']:
            session_data = {
                'client_code': request.client_code,
                'feed_token': mock_feed_token,
                'login_time': datetime.now().isoformat()
            }
            await app_state['redis'].setex(
                f"session:{request.client_code}",
                86400,
                json.dumps(session_data)
            )
        
        return LoginResponse(
            success=True,
            message="Login successful (mock)",
            data={'client_code': request.client_code, 'feed_token': mock_feed_token}
        )
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/auth/session/{client_code}")
async def get_session(client_code: str):
    """Get active session"""
    try:
        if app_state['redis']:
            session_data = await app_state['redis'].get(f"session:{client_code}")
            if session_data:
                return {"success": True, "data": json.loads(session_data)}
        raise HTTPException(status_code=404, detail="No active session")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get session error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/spot/{symbol}")
async def get_spot_price(symbol: str):
    """Get current spot price"""
    mock_spot = 23456.78 if symbol == "NIFTY" else 48234.56
    return {"symbol": symbol, "spot_price": mock_spot}

@app.get("/api/option-chain/{symbol}")
async def get_option_chain(symbol: str):
    """Get option chain"""
    return generate_mock_option_chain(symbol)

# WebSocket
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        if client_id not in self.active_connections:
            self.active_connections[client_id] = []
        self.active_connections[client_id].append(websocket)
        logger.info(f"✅ Client {client_id} connected")
    
    def disconnect(self, websocket: WebSocket, client_id: str):
        if client_id in self.active_connections:
            self.active_connections[client_id].remove(websocket)
            if not self.active_connections[client_id]:
                del self.active_connections[client_id]
        logger.info(f"❌ Client {client_id} disconnected")
    
    async def broadcast_to_client(self, client_id: str, data: dict):
        if client_id in self.active_connections:
            message = json.dumps(data)
            for connection in self.active_connections[client_id]:
                try:
                    await connection.send_text(message)
                except Exception as e:
                    logger.error(f"Broadcast error: {e}")

manager = ConnectionManager()

@app.websocket("/ws/{symbol}/{client_code}")
async def websocket_endpoint(websocket: WebSocket, symbol: str, client_code: str):
    """WebSocket endpoint"""
    await manager.connect(websocket, client_code)
    
    try:
        await websocket.send_json({
            "type": "connected",
            "message": f"Connected to {symbol} option chain (mock data)"
        })
        
        async def broadcast_loop():
            while True:
                try:
                    data = generate_mock_option_chain(symbol)
                    await manager.broadcast_to_client(client_code, {
                        "type": "update",
                        "data": data
                    })
                    await asyncio.sleep(1)
                except Exception as e:
                    logger.error(f"Broadcast loop error: {e}")
                    await asyncio.sleep(1)
        
        broadcast_task = asyncio.create_task(broadcast_loop())
        
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                if message.get('type') == 'ping':
                    await websocket.send_json({"type": "pong"})
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                break
        
        broadcast_task.cancel()
    except Exception as e:
        logger.error(f"WebSocket endpoint error: {e}")
    finally:
        manager.disconnect(websocket, client_code)

@app.get("/health")
async def health_check():
    """Health check"""
    redis_status = "disconnected"
    if app_state['redis']:
        try:
            await app_state['redis'].ping()
            redis_status = "connected"
        except:
            redis_status = "error"
    
    return {
        "status": "healthy",
        "redis": redis_status,
        "active_connections": len(manager.active_connections),
        "timestamp": datetime.now().isoformat()
    }

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "F&O Dashboard API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }
