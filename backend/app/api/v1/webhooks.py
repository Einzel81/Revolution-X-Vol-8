"""
Webhook handlers for external integrations
"""
import logging
from typing import Dict, Any
from fastapi import APIRouter, Request, HTTPException, Depends, BackgroundTasks
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.security import verify_webhook_signature
from app.telegram.bot import telegram_bot
from app.services.notification_service import notification_service
from app.alerts.trade_alerts import trade_alert_manager
from app.alerts.risk_alerts import risk_alert_manager

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/telegram")
async def telegram_webhook(request: Request):
    """
    Handle Telegram webhook updates
    """
    try:
        # Verify request is from Telegram (optional, based on IP or secret)
        data = await request.json()
        
        logger.debug(f"Received Telegram webhook: {data}")
        
        # Process update
        await telegram_bot.process_update(data)
        
        return JSONResponse(content={"ok": True})
        
    except Exception as e:
        logger.error(f"Error processing Telegram webhook: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/tradingview")
async def tradingview_webhook(
    request: Request,
    background_tasks: BackgroundTasks
):
    """
    Handle TradingView webhook alerts
    """
    try:
        # Verify signature if configured
        if settings.TRADINGVIEW_WEBHOOK_SECRET:
            signature = request.headers.get('X-Signature')
            body = await request.body()
            if not verify_webhook_signature(body, signature, settings.TRADINGVIEW_WEBHOOK_SECRET):
                raise HTTPException(status_code=401, detail="Invalid signature")
        
        data = await request.json()
        
        logger.info(f"Received TradingView alert: {data}")
        
        # Process alert in background
        background_tasks.add_task(process_tradingview_alert, data)
        
        return JSONResponse(content={"status": "received", "alert_id": data.get('id')})
        
    except Exception as e:
        logger.error(f"Error processing TradingView webhook: {e}")
        raise HTTPException(status_code=500, detail="Failed to process alert")


@router.post("/exchange")
async def exchange_webhook(request: Request):
    """
    Handle exchange webhooks (order updates, etc.)
    """
    try:
        data = await request.json()
        event_type = data.get('event')
        
        logger.info(f"Received exchange webhook: {event_type}")
        
        if event_type == 'order_filled':
            await handle_order_filled(data)
        elif event_type == 'liquidation_warning':
            await handle_liquidation_warning(data)
        elif event_type == 'margin_call':
            await handle_margin_call(data)
        
        return JSONResponse(content={"status": "processed"})
        
    except Exception as e:
        logger.error(f"Error processing exchange webhook: {e}")
        raise HTTPException(status_code=500, detail="Failed to process webhook")


@router.post("/stripe")
async def stripe_webhook(request: Request):
    """
    Handle Stripe payment webhooks
    """
    try:
        payload = await request.body()
        sig_header = request.headers.get('stripe-signature')
        
        # Verify webhook signature
        # event = stripe.Webhook.construct_event(
        #     payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        # )
        
        logger.info("Received Stripe webhook")
        
        # Handle event types
        # if event['type'] == 'invoice.paid':
        #     await handle_subscription_paid(event['data']['object'])
        
        return JSONResponse(content={"status": "success"})
        
    except Exception as e:
        logger.error(f"Stripe webhook error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


async def process_tradingview_alert(data: Dict[str, Any]):
    """Process TradingView alert in background"""
    try:
        symbol = data.get('symbol')
        action = data.get('action')  # buy, sell, alert
        price = data.get('price')
        
        # Notify users subscribed to this symbol
        # Implementation depends on your alert subscription system
        
        logger.info(f"Processed TradingView alert for {symbol}: {action}")
        
    except Exception as e:
        logger.error(f"Failed to process TradingView alert: {e}")


async def handle_order_filled(data: Dict[str, Any]):
    """Handle order filled event from exchange"""
    try:
        order_id = data.get('order_id')
        user_id = data.get('user_id')
        
        # Send notification
        await notification_service.send_notification(
            user_id=user_id,
            notification_type='order_filled',
            title="Order Filled",
            message=f"Order {order_id} has been filled",
            data=data
        )
        
    except Exception as e:
        logger.error(f"Failed to handle order filled: {e}")


async def handle_liquidation_warning(data: Dict[str, Any]):
    """Handle liquidation warning"""
    try:
        user_id = data.get('user_id')
        symbol = data.get('symbol')
        
        await risk_alert_manager.check_margin_level(user_id, {
            'used_margin_percent': data.get('margin_used', 0),
            'symbol': symbol
        })
        
    except Exception as e:
        logger.error(f"Failed to handle liquidation warning: {e}")


async def handle_margin_call(data: Dict[str, Any]):
    """Handle margin call event"""
    try:
        user_id = data.get('user_id')
        
        await risk_alert_manager.check_margin_level(user_id, {
            'used_margin_percent': 90,  # Critical level
            'margin_call': True
        })
        
    except Exception as e:
        logger.error(f"Failed to handle margin call: {e}")


@router.get("/health")
async def webhook_health():
    """Health check for webhooks"""
    return {
        "status": "operational",
        "telegram": "active",
        "tradingview": "active",
        "exchange": "active"
    }
