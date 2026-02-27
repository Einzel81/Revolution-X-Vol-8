"""
Alert Manager - Smart alerts and triggers
"""
import logging
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from app.core.database import get_db
from app.models.alert import Alert, AlertType, AlertCondition
from app.models.user import User
from app.services.notification_service import notification_service, NotificationPriority
from app.telegram.bot import telegram_bot

logger = logging.getLogger(__name__)


class AlertTrigger(Enum):
    PRICE_ABOVE = "price_above"
    PRICE_BELOW = "price_below"
    PRICE_CHANGE_PERCENT = "price_change_percent"
    VOLUME_SPIKE = "volume_spike"
    DRAWDOWN_PERCENT = "drawdown_percent"
    CONSECUTIVE_LOSSES = "consecutive_losses"
    PROFIT_TARGET = "profit_target"
    LOSS_LIMIT = "loss_limit"
    MARGIN_LEVEL = "margin_level"
    NEWS_KEYWORD = "news_keyword"


@dataclass
class AlertConfig:
    """Alert configuration"""
    user_id: int
    alert_type: AlertType
    trigger: AlertTrigger
    symbol: Optional[str]
    condition_value: float
    message_template: str
    is_active: bool = True
    cooldown_minutes: int = 60
    notification_channels: List[str] = None
    
    def __post_init__(self):
        if self.notification_channels is None:
            self.notification_channels = ["telegram"]


class AlertManager:
    """Manage smart alerts"""
    
    def __init__(self):
        self.active_alerts: Dict[int, List[AlertConfig]] = {}
        self.last_triggered: Dict[str, datetime] = {}
        self.price_cache: Dict[str, Dict[str, Any]] = {}
    
    async def create_alert(
        self,
        user_id: int,
        alert_type: AlertType,
        trigger: AlertTrigger,
        condition_value: float,
        symbol: Optional[str] = None,
        message_template: Optional[str] = None,
        cooldown_minutes: int = 60
    ) -> Alert:
        """Create new alert"""
        
        if message_template is None:
            message_template = self._get_default_template(trigger)
        
        alert = Alert(
            user_id=user_id,
            type=alert_type,
            trigger=trigger.value,
            symbol=symbol,
            condition_value=condition_value,
            message_template=message_template,
            cooldown_minutes=cooldown_minutes,
            is_active=True,
            created_at=datetime.utcnow()
        )
        
        async with get_db() as db:
            db.add(alert)
            await db.commit()
            await db.refresh(alert)
        
        # Cache the alert
        if user_id not in self.active_alerts:
            self.active_alerts[user_id] = []
        
        config = AlertConfig(
            user_id=user_id,
            alert_type=alert_type,
            trigger=trigger,
            symbol=symbol,
            condition_value=condition_value,
            message_template=message_template,
            cooldown_minutes=cooldown_minutes
        )
        self.active_alerts[user_id].append(config)
        
        logger.info(f"Alert created for user {user_id}: {trigger.value}")
        return alert
    
    async def check_price_alerts(self, symbol: str, current_price: float, price_data: Dict[str, Any]):
        """Check all price-based alerts"""
        self.price_cache[symbol] = {
            'price': current_price,
            'data': price_data,
            'timestamp': datetime.utcnow()
        }
        
        for user_id, alerts in self.active_alerts.items():
            for alert in alerts:
                if not alert.is_active:
                    continue
                
                if alert.symbol and alert.symbol != symbol:
                    continue
                
                should_trigger = False
                
                if alert.trigger == AlertTrigger.PRICE_ABOVE:
                    should_trigger = current_price >= alert.condition_value
                elif alert.trigger == AlertTrigger.PRICE_BELOW:
                    should_trigger = current_price <= alert.condition_value
                elif alert.trigger == AlertTrigger.PRICE_CHANGE_PERCENT:
                    change = price_data.get('change_24h', 0)
                    should_trigger = abs(change) >= alert.condition_value
                
                if should_trigger:
                    await self._trigger_alert(alert, {
                        'symbol': symbol,
                        'current_price': current_price,
                        'condition_value': alert.condition_value
                    })
    
    async def check_risk_alerts(self, user_id: int, account_data: Dict[str, Any]):
        """Check risk-based alerts"""
        if user_id not in self.active_alerts:
            return
        
        for alert in self.active_alerts[user_id]:
            if not alert.is_active:
                continue
            
            should_trigger = False
            context = {}
            
            if alert.trigger == AlertTrigger.DRAWDOWN_PERCENT:
                drawdown = account_data.get('drawdown_percent', 0)
                should_trigger = drawdown >= alert.condition_value
                context = {
                    'drawdown_percent': drawdown,
                    'loss_amount': account_data.get('loss_amount', 0)
                }
            
            elif alert.trigger == AlertTrigger.CONSECUTIVE_LOSSES:
                consecutive = account_data.get('consecutive_losses', 0)
                should_trigger = consecutive >= alert.condition_value
                context = {
                    'count': consecutive,
                    'total_loss': account_data.get('total_loss', 0),
                    'strategy': account_data.get('strategy', 'N/A')
                }
            
            elif alert.trigger == AlertTrigger.MARGIN_LEVEL:
                margin = account_data.get('margin_level', 100)
                should_trigger = margin <= alert.condition_value
                context = {
                    'available_margin': margin,
                    'used_margin': 100 - margin
                }
            
            if should_trigger:
                await self._trigger_alert(alert, context)
    
    async def check_profit_alerts(self, user_id: int, profit_data: Dict[str, Any]):
        """Check profit/loss alerts"""
        if user_id not in self.active_alerts:
            return
        
        for alert in self.active_alerts[user_id]:
            if not alert.is_active:
                continue
            
            should_trigger = False
            context = {}
            
            if alert.trigger == AlertTrigger.PROFIT_TARGET:
                daily_profit = profit_data.get('daily_pnl', 0)
                should_trigger = daily_profit >= alert.condition_value
                context = {'profit': daily_profit}
            
            elif alert.trigger == AlertTrigger.LOSS_LIMIT:
                daily_loss = profit_data.get('daily_pnl', 0)
                should_trigger = daily_loss <= -alert.condition_value
                context = {'loss': abs(daily_loss)}
            
            if should_trigger:
                await self._trigger_alert(alert, context)
    
    async def _trigger_alert(self, alert: AlertConfig, context: Dict[str, Any]):
        """Trigger alert if not in cooldown"""
        alert_key = f"{alert.user_id}:{alert.alert_type}:{alert.symbol}:{alert.trigger.value}"
        
        # Check cooldown
        if alert_key in self.last_triggered:
            last_time = self.last_triggered[alert_key]
            cooldown = timedelta(minutes=alert.cooldown_minutes)
            if datetime.utcnow() - last_time < cooldown:
                return
        
        self.last_triggered[alert_key] = datetime.utcnow()
        
        # Format message
        message = alert.message_template.format(**context)
        
        # Determine priority
        priority = self._get_priority(alert.alert_type)
        
        # Send notification
        await notification_service.send_notification(
            user_id=alert.user_id,
            notification_type=alert.alert_type,
            title=f"🚨 تنبيه: {alert.trigger.value}",
            message=message,
            data=context,
            priority=priority,
            channels=[notification_service.NotificationChannel.TELEGRAM]
        )
        
        logger.info(f"Alert triggered for user {alert.user_id}: {alert.trigger.value}")
    
    def _get_default_template(self, trigger: AlertTrigger) -> str:
        """Get default message template for trigger"""
        templates = {
            AlertTrigger.PRICE_ABOVE: "🟢 {symbol} تجاوز السعر المستهدف!\nالسعر الحالي: ${current_price:,.2f}\nالهدف: ${condition_value:,.2f}",
            AlertTrigger.PRICE_BELOW: "🔴 {symbol} أقل من السعر المستهدف!\nالسعر الحالي: ${current_price:,.2f}\nالهدف: ${condition_value:,.2f}",
            AlertTrigger.PRICE_CHANGE_PERCENT: "⚡ {symbol} تغير حاد!\nالتغير: {change_24h:+.2f}%",
            AlertTrigger.DRAWDOWN_PERCENT: "🚨 انخفاض حاد في الحساب!\nالانخفاض: {drawdown_percent}%",
            AlertTrigger.CONSECUTIVE_LOSSES: "⚠️ خسائر متتالية!\nالعدد: {count}\nالخسارة: ${total_loss:,.2f}",
            AlertTrigger.PROFIT_TARGET: "🎯 هدف الربح اليومي محقق!\nالربح: ${profit:,.2f}",
            AlertTrigger.LOSS_LIMIT: "🛑 تم الوصول لحد الخسارة اليومي!\nالخسارة: ${loss:,.2f}",
            AlertTrigger.MARGIN_LEVEL: "⚠️ مستوى الهامش منخفض!\nالمتاح: {available_margin}%",
        }
        return templates.get(trigger, "Alert triggered: {trigger}")
    
    def _get_priority(self, alert_type: AlertType) -> NotificationPriority:
        """Get notification priority based on alert type"""
        priority_map = {
            AlertType.RISK: NotificationPriority.HIGH,
            AlertType.MARGIN_CALL: NotificationPriority.HIGH,
            AlertType.EMERGENCY: NotificationPriority.HIGH,
            AlertType.TRADE: NotificationPriority.MEDIUM,
            AlertType.PRICE: NotificationPriority.MEDIUM,
            AlertType.SYSTEM: NotificationPriority.LOW,
            AlertType.PERFORMANCE: NotificationPriority.LOW,
        }
        return priority_map.get(alert_type, NotificationPriority.MEDIUM)
    
    async def load_user_alerts(self, user_id: int):
        """Load active alerts for user from database"""
        async with get_db() as db:
            alerts = await db.query(Alert).filter(
                Alert.user_id == user_id,
                Alert.is_active == True
            ).all()
        
        self.active_alerts[user_id] = []
        for alert in alerts:
            config = AlertConfig(
                user_id=alert.user_id,
                alert_type=alert.type,
                trigger=AlertTrigger(alert.trigger),
                symbol=alert.symbol,
                condition_value=alert.condition_value,
                message_template=alert.message_template,
                cooldown_minutes=alert.cooldown_minutes,
                is_active=alert.is_active
            )
            self.active_alerts[user_id].append(config)
        
        logger.info(f"Loaded {len(alerts)} alerts for user {user_id}")
    
    async def deactivate_alert(self, alert_id: int) -> bool:
        """Deactivate specific alert"""
        async with get_db() as db:
            alert = await db.query(Alert).filter(Alert.id == alert_id).first()
            if alert:
                alert.is_active = False
                await db.commit()
                
                # Remove from cache
                if alert.user_id in self.active_alerts:
                    self.active_alerts[alert.user_id] = [
                        a for a in self.active_alerts[alert.user_id]
                        if not (a.symbol == alert.symbol and 
                               a.trigger.value == alert.trigger and
                               a.condition_value == alert.condition_value)
                    ]
                return True
        return False
    
    async def get_user_alerts(self, user_id: int) -> List[Alert]:
        """Get all alerts for user"""
        async with get_db() as db:
            return await db.query(Alert).filter(Alert.user_id == user_id).all()


# Global instance
alert_manager = AlertManager()
