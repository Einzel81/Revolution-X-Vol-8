"""
Notification Service - Queue-based notifications with Celery
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum

from celery import Celery
from celery.exceptions import MaxRetriesExceededError

from app.core.config import settings
from app.core.database import get_db
from app.models.notification import Notification, NotificationType, NotificationPriority
from app.models.user import User
from app.telegram.bot import telegram_bot

logger = logging.getLogger(__name__)

# Initialize Celery
celery_app = Celery(
    'notifications',
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 minutes
    worker_prefetch_multiplier=1,
    task_acks_late=True,
)

# Periodic tasks schedule (Celery Beat)
celery_app.conf.beat_schedule = {
    "refresh-dxy-context": {
        "task": "app.market_data.dxy_tasks.refresh_dxy_context",
        "schedule": 30.0,  # dynamic refresh inside the task
    },
    "scanner-run": {
        "task": "app.scanner.scanner_tasks.scanner_run",
        "schedule": 120.0,
    },
    "train-models-daily": {
        "task": "app.ai.training.tasks.train_models",
        "schedule": 86400.0,  # once per day
    },
    "predictive-run-6h": {
    "task": "app.predictive.tasks.predictive_run",
    "schedule": 21600.0  # ?? 6 ?????
    },
    "scanner-auto-select-1m": {
    "task": "scanner.auto_select",
    "schedule": 60.0
    },
}
# Ensure tasks are registered
from app.market_data import dxy_tasks  # noqa: F401
from app.scanner import scanner_tasks  # noqa: F401
from app.ai.training import tasks as ai_training_tasks  # noqa: F401
from app.predictive import tasks as predictive_tasks  # noqa: F401

class NotificationChannel(Enum):
    TELEGRAM = "telegram"
    EMAIL = "email"
    IN_APP = "in_app"
    PUSH = "push"
    SMS = "sms"


class NotificationService:
    """Main notification service"""
    
    def __init__(self):
        self.rate_limits = {}
        self.max_notifications_per_minute = 30
    
    async def send_notification(
        self,
        user_id: int,
        notification_type: NotificationType,
        title: str,
        message: str,
        data: Optional[Dict[str, Any]] = None,
        priority: NotificationPriority = NotificationPriority.MEDIUM,
        channels: Optional[List[NotificationChannel]] = None
    ) -> bool:
        """
        Send notification through specified channels
        
        Args:
            user_id: Target user ID
            notification_type: Type of notification
            title: Notification title
            message: Notification message
            data: Additional data
            priority: Priority level
            channels: List of channels to use (default: all available)
        """
        if channels is None:
            channels = [NotificationChannel.TELEGRAM, NotificationChannel.IN_APP]
        
        # Check rate limiting
        if not self._check_rate_limit(user_id):
            logger.warning(f"Rate limit exceeded for user {user_id}")
            return False
        
        # Create notification record
        notification = Notification(
            user_id=user_id,
            type=notification_type,
            title=title,
            message=message,
            data=data or {},
            priority=priority,
            channels=[c.value for c in channels],
            created_at=datetime.utcnow(),
            read=False
        )
        
        # Save to database
        async with get_db() as db:
            db.add(notification)
            await db.commit()
        
        # Queue notification tasks based on priority
        for channel in channels:
            task = self._get_task_by_channel(channel)
            if task:
                task.apply_async(
                    args=[user_id, title, message, data],
                    priority=self._get_celery_priority(priority),
                    countdown=self._get_delay_by_priority(priority)
                )
        
        logger.info(f"Notification queued for user {user_id}: {title}")
        return True
    
    def _check_rate_limit(self, user_id: int) -> bool:
        """Check if user has exceeded rate limit"""
        now = datetime.utcnow()
        key = f"rate_limit:{user_id}"
        
        # This is simplified - in production use Redis
        if key not in self.rate_limits:
            self.rate_limits[key] = []
        
        # Clean old entries
        self.rate_limits[key] = [
            t for t in self.rate_limits[key]
            if (now - t).seconds < 60
        ]
        
        if len(self.rate_limits[key]) >= self.max_notifications_per_minute:
            return False
        
        self.rate_limits[key].append(now)
        return True
    
    def _get_celery_priority(self, priority: NotificationPriority) -> int:
        """Convert priority to Celery priority"""
        priority_map = {
            NotificationPriority.HIGH: 0,
            NotificationPriority.MEDIUM: 5,
            NotificationPriority.LOW: 9
        }
        return priority_map.get(priority, 5)
    
    def _get_delay_by_priority(self, priority: NotificationPriority) -> int:
        """Get delay in seconds based on priority"""
        delay_map = {
            NotificationPriority.HIGH: 0,
            NotificationPriority.MEDIUM: 5,
            NotificationPriority.LOW: 30
        }
        return delay_map.get(priority, 5)
    
    def _get_task_by_channel(self, channel: NotificationChannel):
        """Get Celery task for specific channel"""
        task_map = {
            NotificationChannel.TELEGRAM: send_telegram_notification,
            NotificationChannel.EMAIL: send_email_notification,
            NotificationChannel.IN_APP: None  # In-app is immediate
        }
        return task_map.get(channel)
    
    async def broadcast_notification(
        self,
        notification_type: NotificationType,
        title: str,
        message: str,
        data: Optional[Dict[str, Any]] = None,
        priority: NotificationPriority = NotificationPriority.MEDIUM,
        user_filter: Optional[Dict[str, Any]] = None
    ) -> Dict[int, bool]:
        """
        Broadcast notification to multiple users
        
        Args:
            user_filter: Filter criteria for users (e.g., {'is_active': True})
        """
        async with get_db() as db:
            query = db.query(User)
            if user_filter:
                for key, value in user_filter.items():
                    query = query.filter(getattr(User, key) == value)
            
            users = await query.all()
        
        results = {}
        for user in users:
            result = await self.send_notification(
                user_id=user.id,
                notification_type=notification_type,
                title=title,
                message=message,
                data=data,
                priority=priority
            )
            results[user.id] = result
        
        return results
    
    async def get_user_notifications(
        self,
        user_id: int,
        unread_only: bool = False,
        limit: int = 50,
        offset: int = 0
    ) -> List[Notification]:
        """Get notifications for user"""
        async with get_db() as db:
            query = db.query(Notification).filter(Notification.user_id == user_id)
            
            if unread_only:
                query = query.filter(Notification.read == False)
            
            query = query.order_by(Notification.created_at.desc())
            query = query.offset(offset).limit(limit)
            
            return await query.all()
    
    async def mark_as_read(self, notification_id: int, user_id: int) -> bool:
        """Mark notification as read"""
        async with get_db() as db:
            notification = await db.query(Notification).filter(
                Notification.id == notification_id,
                Notification.user_id == user_id
            ).first()
            
            if notification:
                notification.read = True
                notification.read_at = datetime.utcnow()
                await db.commit()
                return True
            return False
    
    async def mark_all_as_read(self, user_id: int) -> int:
        """Mark all notifications as read"""
        async with get_db() as db:
            result = await db.query(Notification).filter(
                Notification.user_id == user_id,
                Notification.read == False
            ).update({
                'read': True,
                'read_at': datetime.utcnow()
            })
            await db.commit()
            return result


# Celery Tasks
@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def send_telegram_notification(self, user_id: int, title: str, message: str, data: Dict[str, Any]):
    """Send Telegram notification"""
    try:
        import asyncio
        
        async def _send():
            await telegram_bot.initialize()
            
            # Get user's Telegram chat ID
            async with get_db() as db:
                from app.models.telegram_user import TelegramUser
                telegram_user = await db.query(TelegramUser).filter(
                    TelegramUser.user_id == user_id,
                    TelegramUser.is_active == True
                ).first()
                
                if not telegram_user:
                    logger.warning(f"No Telegram connection for user {user_id}")
                    return False
                
                # Send message
                full_message = f"<b>{title}</b>\n\n{message}"
                success = await telegram_bot.send_message(
                    chat_id=telegram_user.chat_id,
                    text=full_message
                )
                
                return success
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(_send())
        loop.close()
        
        if not result:
            raise Exception("Failed to send Telegram message")
        
        return result
        
    except Exception as exc:
        logger.error(f"Telegram notification failed: {exc}")
        try:
            self.retry(exc=exc)
        except MaxRetriesExceededError:
            logger.error(f"Max retries exceeded for user {user_id}")
            return False


@celery_app.task(bind=True, max_retries=3, default_retry_delay=300)
def send_email_notification(self, user_id: int, title: str, message: str, data: Dict[str, Any]):
    """Send email notification"""
    try:
        # Implement email sending logic here
        # This is a placeholder
        logger.info(f"Email notification would be sent to user {user_id}: {title}")
        return True
        
    except Exception as exc:
        logger.error(f"Email notification failed: {exc}")
        try:
            self.retry(exc=exc)
        except MaxRetriesExceededError:
            return False


# Global service instance
notification_service = NotificationService()
