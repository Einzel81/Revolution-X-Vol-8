"""
Risk Alerts - Risk management notifications
"""
import logging
from typing import Dict, Any, List
from datetime import datetime, timedelta

from app.core.database import get_db
from app.models.user import User
from app.telegram.bot import telegram_bot
from app.services.notification_service import notification_service, NotificationPriority, NotificationChannel
from app.services.alert_manager import alert_manager, AlertTrigger, AlertType

logger = logging.getLogger(__name__)


class RiskAlertManager:
    """Manage risk-related alerts"""
    
    def __init__(self):
        self.risk_thresholds = {
            'drawdown_warning': 10.0,  # 10%
            'drawdown_critical': 20.0,  # 20%
            'consecutive_losses': 3,
            'daily_loss_limit': 5.0,  # 5% of account
            'margin_warning': 50.0,  # 50% used
            'margin_critical': 80.0,  # 80% used
        }
        self.alert_cooldowns = {}
    
    async def check_drawdown(self, user_id: int, account_data: Dict[str, Any]):
        """Check account drawdown"""
        current_drawdown = account_data.get('drawdown_percent', 0)
        
        if current_drawdown >= self.risk_thresholds['drawdown_critical']:
            await self._send_drawdown_alert(user_id, current_drawdown, 'critical')
        elif current_drawdown >= self.risk_thresholds['drawdown_warning']:
            await self._send_drawdown_alert(user_id, current_drawdown, 'warning')
    
    async def _send_drawdown_alert(self, user_id: int, drawdown: float, level: str):
        """Send drawdown alert"""
        if not self._check_cooldown(user_id, 'drawdown'):
            return
        
        emoji = "🚨" if level == 'critical' else "⚠️"
        
        message = f"""
{emoji} <b>تنبيه انخفاض الحساب - Drawdown Alert</b>

📉 <b>نسبة الانخفاض:</b> {drawdown:.2f}%
🔴 <b>المستوى:</b> {level.upper()}

⚡ <b>الإجراءات الموصى بها:</b>
• مراجعة الصفقات المفتوحة فوراً
• تفعيل وقف الخسارة لجميع الصفقات
• تقليل حجم المراكز بنسبة 50%
• إيقاف فتح صفقات جديدة مؤقتاً

🤖 <b>AI Guardian:</b> تم تفعيل وضع الحماية التلقائية
        """
        
        # Send via Telegram
        async with get_db() as db:
            from app.models.telegram_user import TelegramUser
            telegram_user = await db.query(TelegramUser).filter(
                TelegramUser.user_id == user_id,
                TelegramUser.is_active == True
            ).first()
            
            if telegram_user:
                await telegram_bot.send_message(
                    chat_id=telegram_user.chat_id,
                    text=message
                )
        
        # Send high priority notification
        await notification_service.send_notification(
            user_id=user_id,
            notification_type='risk_drawdown',
            title=f"{emoji} Drawdown Alert: {drawdown:.1f}%",
            message=f"Account drawdown reached {drawdown:.2f}%",
            data={'drawdown': drawdown, 'level': level},
            priority=NotificationPriority.HIGH,
            channels=[NotificationChannel.IN_APP, NotificationChannel.TELEGRAM]
        )
        
        self._set_cooldown(user_id, 'drawdown', minutes=30 if level == 'warning' else 10)
        logger.warning(f"Drawdown alert sent to user {user_id}: {drawdown}%")
    
    async def check_consecutive_losses(self, user_id: int, trades_data: Dict[str, Any]):
        """Check for consecutive losses"""
        consecutive = trades_data.get('consecutive_losses', 0)
        
        if consecutive >= self.risk_thresholds['consecutive_losses']:
            await self._send_consecutive_losses_alert(user_id, consecutive, trades_data)
    
    async def _send_consecutive_losses_alert(self, user_id: int, count: int, data: Dict[str, Any]):
        """Send consecutive losses alert"""
        if not self._check_cooldown(user_id, 'consecutive_losses'):
            return
        
        message = f"""
⚠️ <b>تنبيه خسائر متتالية - Consecutive Losses</b>

🔴 <b>عدد الخسائر المتتالية:</b> {count}
💰 <b>إجمالي الخسارة:</b> ${data.get('total_loss', 0):,.2f}
🎯 <b>الاستراتيجية:</b> {data.get('strategy', 'N/A')}

💡 <b>توصيات AI Guardian:</b>
1. إيقاف التداول لمدة 30 دقيقة
2. مراجعة إعدادات الاستراتيجية
3. تقليل حجم الصفقات إلى 50%
4. التحقق من ظروف السوق العامة

⚙️ <b>الإجراء التلقائي:</b>
• تم تقليل المخاطرة تلقائياً
• تم تفعيل فلتر إضافي للصفقات
        """
        
        async with get_db() as db:
            from app.models.telegram_user import TelegramUser
            telegram_user = await db.query(TelegramUser).filter(
                TelegramUser.user_id == user_id,
                TelegramUser.is_active == True
            ).first()
            
            if telegram_user:
                await telegram_bot.send_message(
                    chat_id=telegram_user.chat_id,
                    text=message
                )
        
        await notification_service.send_notification(
            user_id=user_id,
            notification_type='risk_consecutive_losses',
            title=f"⚠️ {count} Consecutive Losses",
            message=f"Total loss: ${data.get('total_loss', 0):,.2f}",
            data=data,
            priority=NotificationPriority.HIGH
        )
        
        self._set_cooldown(user_id, 'consecutive_losses', minutes=60)
        logger.warning(f"Consecutive losses alert sent to user {user_id}: {count}")
    
    async def check_margin_level(self, user_id: int, margin_data: Dict[str, Any]):
        """Check margin level"""
        used_margin = margin_data.get('used_margin_percent', 0)
        
        if used_margin >= self.risk_thresholds['margin_critical']:
            await self._send_margin_alert(user_id, margin_data, 'critical')
        elif used_margin >= self.risk_thresholds['margin_warning']:
            await self._send_margin_alert(user_id, margin_data, 'warning')
    
    async def _send_margin_alert(self, user_id: int, data: Dict[str, Any], level: str):
        """Send margin alert"""
        if not self._check_cooldown(user_id, f'margin_{level}'):
            return
        
        emoji = "🆘" if level == 'critical' else "⚠️"
        used = data.get('used_margin_percent', 0)
        available = 100 - used
        
        message = f"""
{emoji} <b>تنبيه الهامش - Margin Alert</b>

📊 <b>الهامش المستخدم:</b> {used:.1f}%
✅ <b>الهامش المتاح:</b> {available:.1f}%

🚨 <b>خطر التصفية!</b> إذا وصل الهامش المتاح إلى 0%

⚡ <b>الإجراءات المطلوبة:</b>
1. إضافة رصيد للحساب فوراً
2. إغلاق بعض المراكز الخاسرة
3. تقليل الرافعة المالية
4. مراجعة إدارة المخاطر

⛔ <b>الإجراء التلقائي:</b>
• تم إيقاف فتح صفقات جديدة
• تم تفعيل التنبيهات الفورية
        """
        
        async with get_db() as db:
            from app.models.telegram_user import TelegramUser
            telegram_user = await db.query(TelegramUser).filter(
                TelegramUser.user_id == user_id,
                TelegramUser.is_active == True
            ).first()
            
            if telegram_user:
                await telegram_bot.send_message(
                    chat_id=telegram_user.chat_id,
                    text=message
                )
        
        await notification_service.send_notification(
            user_id=user_id,
            notification_type='risk_margin',
            title=f"{emoji} Margin Alert: {used:.1f}% used",
            message=f"Available margin: {available:.1f}%",
            data=data,
            priority=NotificationPriority.HIGH
        )
        
        self._set_cooldown(user_id, f'margin_{level}', minutes=15)
        logger.warning(f"Margin alert sent to user {user_id}: {used}% used")
    
    async def check_daily_limit(self, user_id: int, daily_data: Dict[str, Any]):
        """Check daily profit/loss limits"""
        daily_pnl = daily_data.get('pnl', 0)
        account_balance = daily_data.get('balance', 1)
        pnl_percent = (daily_pnl / account_balance) * 100
        
        # Check loss limit
        if pnl_percent <= -self.risk_thresholds['daily_loss_limit']:
            await self._send_daily_limit_alert(user_id, daily_pnl, pnl_percent, 'loss')
        
        # Check profit target (optional notification)
        elif pnl_percent >= 5:  # 5% profit
            await self._send_daily_limit_alert(user_id, daily_pnl, pnl_percent, 'profit')
    
    async def _send_daily_limit_alert(self, user_id: int, pnl: float, percent: float, limit_type: str):
        """Send daily limit alert"""
        if limit_type == 'loss':
            message = f"""
🛑 <b>تم الوصول لحد الخسارة اليومي</b>

📉 <b>الخسارة:</b> ${abs(pnl):,.2f} ({abs(percent):.2f}%)

⚡ <b>الإجراءات:</b>
• تم إيقاف التداول التلقائي
• مراجعة استراتيجيات اليوم
• تقييم أداء السوق

🤖 <b>AI Guardian:</b> وضع الحماية مفعل
            """
            priority = NotificationPriority.HIGH
            title = "🛑 Daily Loss Limit Reached"
        else:
            message = f"""
🎯 <b>هدف الربح اليومي محقق!</b>

📈 <b>الربح:</b> ${pnl:,.2f} ({percent:.2f}%)

💡 <b>نصيحة:</b> فكر في إيقاف التداول لهذا اليوم
لحماية الأرباح المحققة.

🎉 أحسنت!
            """
            priority = NotificationPriority.MEDIUM
            title = "🎯 Daily Profit Target Reached"
        
        async with get_db() as db:
            from app.models.telegram_user import TelegramUser
            telegram_user = await db.query(TelegramUser).filter(
                TelegramUser.user_id == user_id,
                TelegramUser.is_active == True
            ).first()
            
            if telegram_user:
                await telegram_bot.send_message(
                    chat_id=telegram_user.chat_id,
                    text=message
                )
        
        await notification_service.send_notification(
            user_id=user_id,
            notification_type='risk_daily_limit',
            title=title,
            message=f"PnL: ${pnl:,.2f} ({percent:+.2f}%)",
            data={'pnl': pnl, 'percent': percent, 'type': limit_type},
            priority=priority
        )
    
    def _check_cooldown(self, user_id: int, alert_type: str) -> bool:
        """Check if alert is in cooldown"""
        key = f"{user_id}:{alert_type}"
        if key in self.alert_cooldowns:
            if datetime.utcnow() < self.alert_cooldowns[key]:
                return False
        return True
    
    def _set_cooldown(self, user_id: int, alert_type: str, minutes: int):
        """Set cooldown for alert"""
        key = f"{user_id}:{alert_type}"
        self.alert_cooldowns[key] = datetime.utcnow() + timedelta(minutes=minutes)
    
    async def send_volatility_alert(self, user_id: int, symbol: str, volatility_data: Dict[str, Any]):
        """Send high volatility alert"""
        message = f"""
⚡ <b>تنبيه تقلب عالي - High Volatility</b>

💎 <b>الزوج:</b> {symbol}
📊 <b>التقلب:</b> {volatility_data.get('volatility', 0):.2f}%
📈 <b>التغير:</b> {volatility_data.get('change', 0):+.2f}%

💡 <b>نصائح:</b>
• زيادة مسافة وقف الخسارة
• تقليل حجم الصفقات
• الانتباه للأخبار الاقتصادية
• تجنب فتح صفقات كبيرة
        """
        
        async with get_db() as db:
            from app.models.telegram_user import TelegramUser
            telegram_user = await db.query(TelegramUser).filter(
                TelegramUser.user_id == user_id,
                TelegramUser.is_active == True
            ).first()
            
            if telegram_user:
                await telegram_bot.send_message(
                    chat_id=telegram_user.chat_id,
                    text=message
                )


# Global instance
risk_alert_manager = RiskAlertManager()
