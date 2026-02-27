"""
AI System API Endpoints
Revolution X - Phase 4
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from fastapi.responses import JSONResponse
from typing import List, Optional
from datetime import datetime

from ...ai.ensemble import EnsembleFusion, EnsemblePrediction
from ...ai.scanner import SmartOpportunityScanner, OpportunityScore
from ...dxy_guardian.tracker import DXYTracker
from ...dxy_guardian.correlation import DXYCorrelationAnalyzer

router = APIRouter(prefix="/ai", tags=["AI System"])

# Global instances
ensemble = EnsembleFusion()
scanner = SmartOpportunityScanner(ensemble=ensemble)
dxy_tracker = DXYTracker()
correlation_analyzer = DXYCorrelationAnalyzer()

@router.post("/predict/{symbol}")
async def get_ai_prediction(
    symbol: str,
    timeframe: str = "1h",
    include_features: bool = True
):
    """
    Get AI ensemble prediction for a symbol
    """
    try:
        # Fetch data (mock for now)
        import pandas as pd
        import numpy as np
        
        # Generate mock data for demonstration
        dates = pd.date_range(end=datetime.now(), periods=200, freq='H')
        df = pd.DataFrame({
            'open': np.random.randn(200).cumsum() + 2000,
            'high': np.random.randn(200).cumsum() + 2010,
            'low': np.random.randn(200).cumsum() + 1990,
            'close': np.random.randn(200).cumsum() + 2000,
            'volume': np.random.randint(1000, 10000, 200)
        }, index=dates)
        
        # Get predictions
        lstm_pred = ensemble.lstm.predict(df)
        xgb_pred = ensemble.xgboost.predict(df)
        lgb_pred = ensemble.lightgbm.predict(df, xgboost_signal=xgb_pred.signal)
        
        # Fuse
        result = ensemble.fuse_predictions(lstm_pred, xgb_pred, lgb_pred)
        
        # Trade recommendation
        current_price = df['close'].iloc[-1]
        atr = df['close'].diff().abs().rolling(14).mean().iloc[-1]
        trade_rec = ensemble.get_trade_recommendation(result, current_price, atr)
        
        return {
            "symbol": symbol,
            "timestamp": datetime.now().isoformat(),
            "prediction": {
                "signal": result.final_signal,
                "strength": result.signal_strength.value,
                "confidence": result.confidence,
                "consensus": result.consensus_score,
                "risk_level": result.risk_level
            },
            "models": result.individual_predictions,
            "recommendation": result.recommended_action,
            "trade_details": trade_rec
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/scanner/opportunities")
async def get_scanner_opportunities(
    min_score: float = Query(60.0, ge=0, le=100),
    max_results: int = Query(5, ge=1, le=10)
):
    """
    Get current trading opportunities from scanner
    """
    try:
        # Mock opportunities for demonstration
        opportunities = [
            {
                "symbol": "XAUUSD",
                "name": "Gold",
                "current_price": 2034.50,
                "daily_change": 0.45,
                "ai_score": 87.5,
                "trend_score": 85.0,
                "momentum_score": 90.0,
                "volume_score": 82.0,
                "smc_score": 88.0,
                "risk_level": "low",
                "recommended_action": "BUY",
                "confidence": 0.85,
                "last_update": datetime.now().isoformat()
            },
            {
                "symbol": "XAGUSD",
                "name": "Silver",
                "current_price": 22.85,
                "daily_change": 1.2,
                "ai_score": 78.3,
                "trend_score": 75.0,
                "momentum_score": 82.0,
                "volume_score": 76.0,
                "smc_score": 70.0,
                "risk_level": "medium",
                "recommended_action": "BUY",
                "confidence": 0.78,
                "last_update": datetime.now().isoformat()
            },
            {
                "symbol": "XPTUSD",
                "name": "Platinum",
                "current_price": 915.30,
                "daily_change": -0.3,
                "ai_score": 45.2,
                "trend_score": 40.0,
                "momentum_score": 50.0,
                "volume_score": 45.0,
                "smc_score": 42.0,
                "risk_level": "high",
                "recommended_action": "HOLD",
                "confidence": 0.45,
                "last_update": datetime.now().isoformat()
            }
        ]
        
        # Filter by min_score
        filtered = [o for o in opportunities if o["ai_score"] >= min_score]
        
        return {
            "scan_time": datetime.now().isoformat(),
            "auto_mode": scanner.auto_select,
            "min_threshold": min_score,
            "opportunities": filtered[:max_results],
            "total_found": len(filtered)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/scanner/refresh")
async def refresh_scanner(background_tasks: BackgroundTasks):
    """
    Trigger a new scan of all assets
    """
    # In production, this would run actual scan
    return {
        "message": "Scan initiated",
        "timestamp": datetime.now().isoformat(),
        "assets": list(scanner.ASSETS.keys())
    }

@router.get("/dxy/status")
async def get_dxy_status():
    """
    Get current DXY status and impact on Gold
    """
    status = dxy_tracker.get_status()
    impact = dxy_tracker.get_impact_on_gold()
    
    return {
        "dxy_status": status,
        "gold_impact": impact,
        "timestamp": datetime.now().isoformat()
    }

@router.get("/dxy/correlation")
async def get_dxy_correlation(
    periods: List[str] = Query(["short", "medium", "long"])
):
    """
    Get DXY-Gold correlation analysis
    """
    # Mock correlation data
    return {
        "analysis": {
            "current_correlation": -0.82,
            "correlation_trend": "stable",
            "trading_implications": [
                "Strong inverse correlation - DXY is excellent Gold predictor",
                "Consider DXY as leading indicator for Gold entries"
            ],
            "hedging_recommendation": "Strong hedge potential: Long Gold + Short DXY"
        },
        "timeframes": {
            "short": {
                "correlation": -0.75,
                "regime": "strong_inverse",
                "reliability": "high"
            },
            "medium": {
                "correlation": -0.82,
                "regime": "strong_inverse",
                "reliability": "high"
            },
            "long": {
                "correlation": -0.78,
                "regime": "strong_inverse",
                "reliability": "high"
            }
        }
    }

@router.get("/dxy/alerts")
async def get_dxy_alerts(limit: int = Query(10, ge=1, le=50)):
    """
    Get recent DXY alerts
    """
    alerts = [
        {
            "type": "resistance",
            "price": 104.50,
            "message": "DXY approaching resistance at 104.50",
            "time": datetime.now().isoformat(),
            "severity": "warning"
        },
        {
            "type": "support",
            "price": 103.00,
            "message": "DXY holding support at 103.00",
            "time": datetime.now().isoformat(),
            "severity": "info"
        }
    ]
    
    return {
        "alerts": alerts[:limit],
        "unread_count": len(alerts)
    }

@router.post("/dxy/adjust-signal")
async def adjust_signal_for_dxy(signal_data: dict):
    """
    Adjust a Gold signal based on DXY correlation
    """
    original_signal = signal_data.get("signal", "buy")
    confidence = signal_data.get("confidence", 0.7)
    
    # Mock adjustment
    adjustment = {
        "original_signal": original_signal,
        "adjusted_signal": original_signal,
        "original_confidence": confidence,
        "adjusted_confidence": round(confidence * 0.9, 3),
        "adjustments": ["DXY strength reduces confidence slightly"],
        "correlation_used": -0.82,
        "recommendation": "proceed"
    }
    
    return adjustment

@router.get("/models/status")
async def get_models_status():
    """
    Get status of all AI models
    """
    return {
        "lstm": {
            "status": "active",
            "trained": ensemble.lstm.is_trained,
            "sequence_length": ensemble.lstm.sequence_length,
            "last_prediction": datetime.now().isoformat()
        },
        "xgboost": {
            "status": "active",
            "trained": ensemble.xgboost.is_trained,
            "n_estimators": ensemble.xgboost.n_estimators,
            "last_prediction": datetime.now().isoformat()
        },
        "lightgbm": {
            "status": "active",
            "trained": ensemble.lightgbm.is_trained,
            "n_estimators": ensemble.lightgbm.n_estimators,
            "last_prediction": datetime.now().isoformat()
        },
        "ensemble": {
            "weights": {
                "lstm": ensemble.lstm_weight,
                "xgboost": ensemble.xgboost_weight,
                "lightgbm": ensemble.lightgbm_weight
            },
            "consensus_threshold": ensemble.min_consensus
        }
    }
