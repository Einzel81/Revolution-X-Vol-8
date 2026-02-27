"""
AI Guardian Alerts - Notifications for AI system updates
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from app.core.database import get_db
from app.telegram.bot import telegram_bot
from app.services.notification_service import notification_service, NotificationPriority, NotificationChannel

logger = logging.getLogger(__name__)


class GuardianAlertManager:
    """Manage AI Guardian alerts"""
    
    async def notify_optimization_applied(
        self,
        user_id: int,
        strategy_name: str,
        optimization_data: Dict[str, Any]
    ):
        """Notify when optimization is applied"""
        try:
            message = f"""
🤖 <b>AI Guardian - تحسين جديد</b>

📊 <b>الاستراتيجية:</b> {strategy_name}
⚡ <b>نوع التحسين:</b> {optimization_data.get('type', 'Optimization')}
📈 <b>التوقع:</b> {optimization_data.get('expected_improvement', 'N/A')}

🔧 <b>التغييرات:</b>
{self._format_changes(optimization_data.get('changes', {}))}

✅ <b>الحالة:</b> تم التطبيق تلقائياً
⏰ <b>الوقت:</b> {datetime.now().strftime('%H:%M:%S')}
            """
            
            async with get_db() as db:
                from app.models.telegram_user import TelegramUser
                telegram_user = await db.query(TelegramUser).filter(
                    TelegramUser.user_id == user_id,
                    TelegramUser.is_active == True
                ).first()
                
                if telegram_user and telegram_user.notifications_enabled.get('guardian_updates', True):
                    await telegram_bot.send_message(
                        chat_id=telegram_user.chat_id,
                        text=message
                    )
            
            await notification_service.send_notification(
                user_id=user_id,
                notification_type='guardian_optimization',
                title=f"🤖 Optimization Applied: {strategy_name}",
                message=f"Expected improvement: {optimization_data.get('expected_improvement', 'N/A')}",
                data=optimization_data,
                priority=NotificationPriority.MEDIUM
            )
            
            logger.info(f"Optimization alert sent to user {user_id} for {strategy_name}")
            
        except Exception as e:
            logger.error(f"Failed to send optimization alert: {e}")
    
    async def notify_parameter_change(
        self,
        user_id: int,
        strategy_name: str,
        parameter: str,
        old_value: Any,
        new_value: Any,
        reason: str
    ):
        """Notify when parameters are changed"""
        try:
            message = f"""
🤖 <b>AI Guardian - تعديل معلمات</b>

📊 <b>الاستراتيجية:</b> {strategy_name}
⚙️ <b>المعلم:</b> {parameter}

📝 <b>القيمة القديمة:</b> {old_value}
✅ <b>القيمة الجديدة:</b> {new_value}

💡 <b>السبب:</b> {reason}
⏰ <b>الوقت:</b> {datetime.now().strftime('%H:%M:%S')}
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
                notification_type='guardian_parameter',
                title=f"🤖 Parameter Updated: {strategy_name}",
                message=f"{parameter}: {old_value} → {new_value}",
                data={
                    'strategy': strategy_name,
                    'parameter': parameter,
                    'old': old_value,
                    'new': new_value,
                    'reason': reason
                },
                priority=NotificationPriority.LOW
            )
            
        except Exception as e:
            logger.error(f"Failed to send parameter change alert: {e}")
    
    async def notify_performance_report(
        self,
        user_id: int,
        report_data: Dict[str, Any]
    ):
        """Send periodic performance report"""
        try:
            message = f"""
🤖 <b>AI Guardian - تقرير الأداء</b>

📈 <b>التحسن:</b> {report_data.get('improvement', 'N/A')}
🎯 <b>الصفقات المحسنة:</b> {report_data.get('optimized_trades', 0)}
⚡ <b>معدل النجاح:</b> {report_data.get('success_rate', 0)}%

🏆 <b>أفضل تحسين:</b> {report_data.get('best_improvement', 'N/A')}
📊 <b>الاستراتيجيات:</b> {report_data.get('active_strategies', 0)}

💡 <b>توصيات:</b>
{self._format_recommendations(report_data.get('recommendations', []))}

⏰ <b>الوقت:</b> {datetime.now().strftime('%Y-%m-%d %H:%M')}
            """
            
            async with get_db() as db:
                from app.models.telegram_user import TelegramUser
                telegram_user = await db.query(TelegramUser).filter(
                    TelegramUser.user_id == user_id,
                    TelegramUser.is_active == True
                ).first()
                
                if telegram_user and telegram_user.notifications_enabled.get('performance_reports', True):
                    await telegram_bot.send_message(
                        chat_id=telegram_user.chat_id,
                        text=message
                    )
            
            await notification_service.send_notification(
                user_id=user_id,
                notification_type='guardian_report',
                title="🤖 AI Guardian Performance Report",
                message=f"Improvement: {report_data.get('improvement', 'N/A')}",
                data=report_data,
                priority=NotificationPriority.LOW
            )
            
        except Exception as e:
            logger.error(f"Failed to send performance report: {e}")
    
    async def notify_mode_change(
        self,
        user_id: int,
        old_mode: str,
        new_mode: str,
        reason: str
    ):
        """Notify when Guardian mode changes"""
        try:
            mode_emojis = {
                'conservative': '🛡️',
                'balanced': '⚖️',
                'aggressive': '⚡'
            }
            
            message = f"""
🤖 <b>AI Guardian - تغيير الوضع</b>

{mode_emojis.get(old_mode, '⚪')} <b>الوضع السابق:</b> {old_mode}
{mode_emojis.get(new_mode, '🔵')} <b>الوضع الجديد:</b> {new_mode}

💡 <b>السبب:</b> {reason}

⚙️ <b>الإعدادات الجديدة:</b>
{self._get_mode_settings(new_mode)}

⏰ <b>الوقت:</b> {datetime.now().strftime('%H:%M:%S')}
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
                notification_type='guardian_mode',
                title=f"🤖 Mode Changed: {old_mode} → {new_mode}",
                message=f"Reason: {reason}",
                data={'old': old_mode, 'new': new_mode, 'reason': reason},
                priority=NotificationPriority.MEDIUM
            )
            
        except Exception as e:
            logger.error(f"Failed to send mode change alert: {e}")
    
    async def notify_anomaly_detected(
        self,
        user_id: int,
        anomaly_data: Dict[str, Any]
    ):
        """Notify when market anomaly is detected"""
        try:
            message = f"""
🔍 <b>AI Guardian - اكتشاف شاذ</b>

⚠️ <b>النوع:</b> {anomaly_data.get('type', 'Unknown')}
📊 <b>الشدة:</b> {anomaly_data.get('severity', 'medium')}
💎 <b>الزوج:</b> {anomaly_data.get('symbol', 'N/A')}

📝 <b>الوصف:</b> {anomaly_data.get('description', 'N/A')}

⚡ <b>الإجراء:</b> {anomaly_data.get('action_taken', 'Monitoring')}

⏰ <b>الوقت:</b> {datetime.now().strftime('%H:%M:%S')}
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
                notification_type='guardian_anomaly',
                title=f"🔍 Anomaly Detected: {anomaly_data.get('type', 'Unknown')}",
                message=anomaly_data.get('description', ''),
                data=anomaly_data,
                priority=NotificationPriority.HIGH if anomaly_data.get('severity') == 'high' else NotificationPriority.MEDIUM
            )
            
        except Exception as e:
            logger.error(f"Failed to send anomaly alert: {e}")
    
    def _format_changes(self, changes: Dict[str, Any]) -> str:
        """Format changes dictionary"""
        if not changes:
            return "• لا توجد تفاصيل"
        
        lines = []
        for key, value in changes.items():
            lines.append(f"• {key}: {value}")
        return "\n".join(lines)
    
    def _format_recommendations(self, recommendations: list) -> str:
        """Format recommendations list"""
        if not recommendations:
            return "• لا توجد توصيات خاصة"
        
        return "\n".join([f"• {rec}" for rec in recommendations])
    
    def _get_mode_settings(self, mode: str) -> str:
        """Get settings description for mode"""
        settings = {
            'conservative': "• المخاطرة: منخفضة\n• حجم الصفقات: صغير\n• وقف الخسارة: ضيق",
            'balanced': "• المخاطرة: متوسطة\n• حجم الصفقات: متوسط\n• وقف الخسارة: معتدل",
            'aggressive': "• المخاطرة: عالية\n• حجم الصفقات: كبير\n• وقف الخسارة: واسع"
        }
        return settings.get(mode, "• الإعدادات الافتراضية")


# Global instance
guardian_alert_manager = GuardianAlertManager()
