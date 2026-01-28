"""
F&O Dashboard Backend - FastAPI Application with Real Angel One Integration
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
import pyotp
from SmartApi import SmartConnect
import math

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
    'active_connections': {},
    'smart_api_sessions': {}  # Store SmartAPI instances per client
}

# Instrument tokens (you may need to update these)
INSTRUMENT_TOKENS = {
    "NIFTY": "99926000",
    "BANKNIFTY": "99926009"
}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    try:
        app_state['redis'] = await redis.from_url(
            REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            socket_connect_timeout=5
        )
        logger.info("✅ Redis connected")
        await app_state['redis'].ping()
    except Exception as e:
        logger.error(f"❌ Redis connection failed: {e}")
        app_state['redis'] = None
    yield
    if app_state['redis']:
        await app_state['redis'].close()

app = FastAPI(title="F&O Dashboard API", version="1.0.0", lifespan=lifespan)

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


def get_smart_api(api_key: str) -> SmartConnect:
    """Create SmartConnect instance"""
    return SmartConnect(api_key=api_key)


@app.post("/api/auth/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """Login with real Angel One API"""
    try:
        smart_api = get_smart_api(request.api_key)
        
        # Generate session with Angel One
        data = smart_api.generateSession(
            request.client_code,
            request.password,
            request.totp_token
        )
        
        if data.get('status') == False:
            return LoginResponse(
                success=False, 
                message=data.get('message', 'Login failed')
            )
        
        # Store session in Redis
        feed_token = smart_api.getfeedToken()
        session_data = {
            'client_code': request.client_code,
            'api_key': request.api_key,
            'feed_token': feed_token,
            'auth_token': data.get('data', {}).get('jwtToken', ''),
            'refresh_token': data.get('data', {}).get('refreshToken', ''),
            'login_time': datetime.now().isoformat()
        }
        
        if app_state['redis']:
            await app_state['redis'].setex(
                f"session:{request.client_code}",
                86400,
                json.dumps(session_data)
            )
        
        # Store SmartAPI instance for this client
        app_state['smart_api_sessions'][request.client_code] = {
            'api': smart_api,
            'api_key': request.api_key
        }
        
        return LoginResponse(
            success=True,
            message="Login successful",
            data={'client_code': request.client_code, 'feed_token': feed_token}
        )
        
    except Exception as e:
        logger.error(f"Login error: {e}")
        return LoginResponse(success=False, message=str(e))


async def get_real_option_chain(symbol: str, client_code: str):
    """Fetch real option chain data from Angel One"""
    try:
        # Get SmartAPI instance for this client
        session = app_state['smart_api_sessions'].get(client_code)
        if not session:
            # Try to restore from Redis
            if app_state['redis']:
                session_data = await app_state['redis'].get(f"session:{client_code}")
                if session_data:
                    data = json.loads(session_data)
                    smart_api = get_smart_api(data['api_key'])
                    session = {'api': smart_api, 'api_key': data['api_key']}
                    app_state['smart_api_sessions'][client_code] = session
        
        if not session:
            raise Exception("No active session")
        
        smart_api = session['api']
        
        # Get spot price
        spot_data = smart_api.ltpData("NSE", symbol, INSTRUMENT_TOKENS.get(symbol, ""))
        spot_price = spot_data.get('data', {}).get('ltp', 0)
        
        # Calculate ATM strike
        strike_interval = 50 if symbol == "NIFTY" else 100
        atm_strike = round(spot_price / strike_interval) * strike_interval
        
        # Generate strike range
        num_strikes = 15
        strikes = [atm_strike + (i - num_strikes // 2) * strike_interval for i in range(num_strikes)]
        
        # Get option chain data
        option_chain = []
        expiry = get_current_expiry()  # You need to implement this
        
        for strike in strikes:
            # Fetch CE and PE data
            for opt_type in ['CE', 'PE']:
                try:
                    trading_symbol = f"{symbol}{expiry}{strike}{opt_type}"
                    quote_data = smart_api.ltpData("NFO", trading_symbol, "")
                    oi_data = smart_api.getQuote("NFO", trading_symbol, "")
                    
                    ltp = quote_data.get('data', {}).get('ltp', 0)
                    oi = oi_data.get('data', {}).get('opnInterest', 0)
                    volume = oi_data.get('data', {}).get('tradedVolume', 0)
                    
                    # Calculate Greeks (simplified)
                    iv = calculate_iv(spot_price, strike, ltp, expiry, opt_type)
                    delta, gamma, theta, vega = calculate_greeks(spot_price, strike, iv, expiry, opt_type)
                    
                    option_chain.append({
                        'strike': strike,
                        'option_type': opt_type,
                        'ltp': ltp,
                        'oi': oi,
                        'oi_change': 0,  # Calculate from previous day
                        'volume': volume,
                        'iv': iv,
                        'delta': delta,
                        'gamma': gamma,
                        'theta': theta,
                        'vega': vega,
                    })
                except Exception as e:
                    logger.error(f"Error fetching {trading_symbol}: {e}")
        
        # Calculate metrics
        total_call_oi = sum(opt['oi'] for opt in option_chain if opt['option_type'] == 'CE')
        total_put_oi = sum(opt['oi'] for opt in option_chain if opt['option_type'] == 'PE')
        pcr_oi = round(total_put_oi / total_call_oi, 2) if total_call_oi > 0 else 0
        max_pain = calculate_max_pain(option_chain, strikes)
        net_gex = calculate_gex(option_chain, spot_price)
        
        return {
            'timestamp': datetime.now().isoformat(),
            'symbol': symbol,
            'spot_price': spot_price,
            'expiry': expiry,
            'option_chain': option_chain,
            'pcr_oi': pcr_oi,
            'pcr_volume': 0,
            'max_pain': max_pain,
            'total_call_oi': total_call_oi,
            'total_put_oi': total_put_oi,
            'net_gex': net_gex,
            'call_gex': 0,
            'put_gex': 0,
        }
        
    except Exception as e:
        logger.error(f"Option chain error: {e}")
        raise


def get_current_expiry():
    """Get current weekly expiry (format: 28JAN26)"""
    from datetime import datetime, timedelta
    today = datetime.now()
    days_until_thursday = (3 - today.weekday()) % 7
    if days_until_thursday == 0 and today.hour >= 15:
        days_until_thursday = 7
    expiry_date = today + timedelta(days=days_until_thursday)
    return expiry_date.strftime("%d%b%y").upper()


def calculate_iv(spot, strike, premium, expiry, opt_type):
    """Calculate Implied Volatility using Black-Scholes"""
    # Simplified - use py_vollib for accurate calculation
    try:
        from py_vollib.black_scholes.implied_volatility import implied_volatility
        from py_vollib.black_scholes import black_scholes
        # Calculate time to expiry
        # ... implement properly
        return 15.0  # Placeholder
    except:
        return 15.0


def calculate_greeks(spot, strike, iv, expiry, opt_type):
    """Calculate option Greeks"""
    # Simplified - use py_vollib for accurate calculation
    return (0.5, 0.001, -10.0, 20.0)  # Placeholder


def calculate_max_pain(option_chain, strikes):
    """Calculate Max Pain strike"""
    # Implement max pain calculation
    return strikes[len(strikes) // 2]


def calculate_gex(option_chain, spot):
    """Calculate Gamma Exposure"""
    # Implement GEX calculation
    return 0


# WebSocket with real data
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        if client_id not in self.active_connections:
            self.active_connections[client_id] = []
        self.active_connections[client_id].append(websocket)

    def disconnect(self, websocket: WebSocket, client_id: str):
        if client_id in self.active_connections:
            self.active_connections[client_id].remove(websocket)
            if not self.active_connections[client_id]:
                del self.active_connections[client_id]

    async def broadcast_to_client(self, client_id: str, data: dict):
        if client_id in self.active_connections:
            message = json.dumps(data)
            for connection in self.active_connections[client_id]:
                try:
                    await connection.send_text(message)
                except:
                    pass

manager = ConnectionManager()


@app.websocket("/ws/{symbol}/{client_code}")
async def websocket_endpoint(websocket: WebSocket, symbol: str, client_code: str):
    """WebSocket endpoint with real data"""
    await manager.connect(websocket, client_code)
    try:
        await websocket.send_json({
            "type": "connected",
            "message": f"Connected to {symbol} live option chain"
        })

        async def broadcast_loop():
            while True:
                try:
                    data = await get_real_option_chain(symbol, client_code)
                    await manager.broadcast_to_client(client_code, {
                        "type": "update",
                        "data": data
                    })
                    await asyncio.sleep(1)
                except Exception as e:
                    logger.error(f"Broadcast error: {e}")
                    await asyncio.sleep(5)

        broadcast_task = asyncio.create_task(broadcast_loop())

        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                if message.get('type') == 'ping':
                    await websocket.send_json({"type": "pong"})
            except WebSocketDisconnect:
                break
            except:
                break

        broadcast_task.cancel()
    finally:
        manager.disconnect(websocket, client_code)


@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


@app.get("/")
async def root():
    return {"message": "F&O Dashboard API", "version": "1.0.0"}
