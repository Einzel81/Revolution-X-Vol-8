"""
Trade Alerts - Real-time trade notifications
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from app.core.database import get_db
from app.models.trade import Trade
from app.models.user import User
from app.telegram.bot import telegram_bot
from app.services.notification_service import notification_service, NotificationPriority, NotificationChannel

logger = logging.getLogger(__name__)


class TradeAlertManager:
    """Manage trade-related alerts"""
    
    async def notify_new_trade(self, trade: Trade, user_id: int, chart_image: Optional[bytes] = None):
        """Send new trade alert"""
        try:
            trade_data = {
                'id': trade.id,
                'symbol': trade.symbol,
                'side': trade.side,
                'entry_price': trade.entry_price,
                'size': trade.size,
                'leverage': trade.leverage,
                'take_profit': trade.take_profit,
                'stop_loss': trade.stop_loss,
                'strategy': trade.strategy
            }
            
            # Get user's Telegram
            async with get_db() as db:
                from app.models.telegram_user import TelegramUser
                telegram_user = await db.query(TelegramUser).filter(
                    TelegramUser.user_id == user_id,
                    TelegramUser.is_active == True
                ).first()
                
                if telegram_user and telegram_user.notifications_enabled.get('new_trades', True):
                    await telegram_bot.send_trade_alert(
                        chat_id=telegram_user.chat_id,
                        trade_data=trade_data,
                        chart_image=chart_image
                    )
            
            # Also send in-app notification
            await notification_service.send_notification(
                user_id=user_id,
                notification_type='trade_new',
                title=f"🟢 صفقة جديدة: {trade.symbol}",
                message=f"{trade.side} @ ${trade.entry_price:,.2f}",
                data=trade_data,
                priority=NotificationPriority.MEDIUM,
                channels=[NotificationChannel.IN_APP]
            )
            
            logger.info(f"New trade alert sent for trade {trade.id}")
            
        except Exception as e:
            logger.error(f"Failed to send new trade alert: {e}")
    
    async def notify_trade_closed(
        self,
        trade: Trade,
        user_id: int,
        pnl: float,
        pnl_percent: float,
        close_reason: str = 'manual'
    ):
        """Send trade close alert"""
        try:
            trade_data = {
                'id': trade.id,
                'symbol': trade.symbol,
                'side': trade.side,
                'entry_price': trade.entry_price,
                'exit_price': trade.exit_price,
                'strategy': trade.strategy,
                'close_reason': close_reason,
                'duration': self._format_duration(trade.opened_at, trade.closed_at)
            }
            
            # Telegram notification
            async with get_db() as db:
                from app.models.telegram_user import TelegramUser
                telegram_user = await db.query(TelegramUser).filter(
                    TelegramUser.user_id == user_id,
                    TelegramUser.is_active == True
                ).first()
                
                if telegram_user and telegram_user.notifications_enabled.get('close_trades', True):
                    await telegram_bot.send_trade_close_alert(
                        chat_id=telegram_user.chat_id,
                        trade_data=trade_data,
                        pnl=pnl,
                        pnl_percent=pnl_percent
                    )
            
            # In-app notification
            emoji = "✅" if pnl >= 0 else "❌"
            await notification_service.send_notification(
                user_id=user_id,
                notification_type='trade_closed',
                title=f"{emoji} صفقة مغلقة: {trade.symbol}",
                message=f"PnL: ${pnl:,.2f} ({pnl_percent:+.2f}%)",
                data={**trade_data, 'pnl': pnl, 'pnl_percent': pnl_percent},
                priority=NotificationPriority.HIGH if pnl < 0 else NotificationPriority.MEDIUM,
                channels=[NotificationChannel.IN_APP]
            )
            
            logger.info(f"Trade close alert sent for trade {trade.id}")
            
        except Exception as e:
            logger.error(f"Failed to send trade close alert: {e}")
    
    async def notify_partial_close(
        self,
        trade: Trade,
        user_id: int,
        closed_percent: float,
        realized_pnl: float
    ):
        """Send partial close notification"""
        try:
            trade_data = {
                'symbol': trade.symbol,
                'side': trade.side,
                'remaining_size': trade.remaining_size
            }
            
            async with get_db() as db:
                from app.models.telegram_user import TelegramUser
                telegram_user = await db.query(TelegramUser).filter(
                    TelegramUser.user_id == user_id,
                    TelegramUser.is_active == True
                ).first()
                
                if telegram_user:
                    from app.telegram.messages import MessageTemplates
                    message = MessageTemplates.partial_close(trade_data, closed_percent, realized_pnl)
                    await telegram_bot.send_message(
                        chat_id=telegram_user.chat_id,
                        text=message
                    )
            
            logger.info(f"Partial close alert sent for trade {trade.id}")
            
        except Exception as e:
            logger.error(f"Failed to send partial close alert: {e}")
    
    async def notify_tp_sl_hit(self, trade: Trade, user_id: int, hit_type: str):
        """Notify when TP or SL is hit"""
        pnl = trade.realized_pnl if hasattr(trade, 'realized_pnl') else 0
        pnl_percent = (pnl / (trade.entry_price * trade.size)) * 100 if trade.size else 0
        
        await self.notify_trade_closed(
            trade=trade,
            user_id=user_id,
            pnl=pnl,
            pnl_percent=pnl_percent,
            close_reason=f"{hit_type}_hit"
        )
    
    def _format_duration(self, opened_at: datetime, closed_at: Optional[datetime]) -> str:
        """Format trade duration"""
        if not closed_at:
            return "N/A"
        
        duration = closed_at - opened_at
        hours, remainder = divmod(duration.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        if duration.days > 0:
            return f"{duration.days}d {hours}h"
        elif hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m {seconds}s"


# Global instance
trade_alert_manager = TradeAlertManager()
