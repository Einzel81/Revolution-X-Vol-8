"""
Telegram Bot Core - Revolution X
"""
import logging
from typing import Optional, Dict, Any, List
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters
)
from telegram.constants import ParseMode
import asyncio
from datetime import datetime
import os

from app.core.config import settings
from app.core.database import get_db
from app.models.user import User
from app.telegram.messages import MessageTemplates
from app.telegram.handlers import CommandHandlers, CallbackHandlers

logger = logging.getLogger(__name__)


class TelegramBot:
    """Revolution X Telegram Bot"""
    
    _instance = None
    _lock = asyncio.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self.token = settings.TELEGRAM_BOT_TOKEN
        self.webhook_url = settings.TELEGRAM_WEBHOOK_URL
        self.application: Optional[Application] = None
        self.bot: Optional[Bot] = None
        self._initialized = True
        self._handlers_registered = False
        
    async def initialize(self):
        """Initialize bot application"""
        if self.application is not None:
            return
            
        try:
            self.application = Application.builder().token(self.token).build()
            self.bot = self.application.bot
            
            # Register handlers
            await self._register_handlers()
            
            logger.info("✅ Telegram Bot initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Telegram Bot: {e}")
            raise
    
    async def _register_handlers(self):
        """Register command and callback handlers"""
        if self._handlers_registered:
            return
            
        # Command handlers
        self.application.add_handler(CommandHandler("start", CommandHandlers.start))
        self.application.add_handler(CommandHandler("help", CommandHandlers.help))
        self.application.add_handler(CommandHandler("status", CommandHandlers.status))
        self.application.add_handler(CommandHandler("positions", CommandHandlers.positions))
        self.application.add_handler(CommandHandler("profit", CommandHandlers.profit))
        self.application.add_handler(CommandHandler("balance", CommandHandlers.balance))
        self.application.add_handler(CommandHandler("daily", CommandHandlers.daily_summary))
        self.application.add_handler(CommandHandler("weekly", CommandHandlers.weekly_report))
        self.application.add_handler(CommandHandler("settings", CommandHandlers.settings))
        self.application.add_handler(CommandHandler("connect", CommandHandlers.connect_account))
        self.application.add_handler(CommandHandler("disconnect", CommandHandlers.disconnect_account))
        self.application.add_handler(CommandHandler("alerts", CommandHandlers.manage_alerts))
        self.application.add_handler(CommandHandler("guardian", CommandHandlers.guardian_status))
        
        # Callback query handlers
        self.application.add_handler(CallbackQueryHandler(CallbackHandlers.button_handler))
        
        # Message handler for text
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, CommandHandlers.handle_message))
        
        # Error handler
        self.application.add_error_handler(self._error_handler)
        
        self._handlers_registered = True
        logger.info("✅ Handlers registered")
    
    async def _error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE):
        """Handle errors"""
        logger.error(f"⚠️ Telegram error: {context.error}")
        if isinstance(update, Update) and update.effective_message:
            await update.effective_message.reply_text(
                "⚠️ حدث خطأ. يرجى المحاولة مرة أخرى.\nAn error occurred. Please try again."
            )
    
    async def start_webhook(self):
        """Start bot with webhook"""
        if not self.application:
            await self.initialize()
            
        await self.application.initialize()
        await self.application.start()
        
        # Set webhook
        await self.bot.set_webhook(
            url=self.webhook_url,
            allowed_updates=Update.ALL_TYPES
        )
        
        logger.info(f"🚀 Webhook set to: {self.webhook_url}")
    
    async def stop(self):
        """Stop the bot"""
        if self.application:
            await self.application.stop()
            await self.application.shutdown()
            logger.info("🛑 Telegram Bot stopped")
    
    async def process_update(self, update_data: Dict[str, Any]):
        """Process webhook update"""
        if not self.application:
            await self.initialize()
            
        update = Update.de_json(update_data, self.bot)
        await self.application.process_update(update)
    
    # ==================== Message Sending Methods ====================
    
    async def send_message(
        self,
        chat_id: int,
        text: str,
        parse_mode: str = ParseMode.HTML,
        reply_markup: Optional[InlineKeyboardMarkup] = None,
        disable_notification: bool = False
    ) -> bool:
        """Send text message"""
        try:
            await self.bot.send_message(
                chat_id=chat_id,
                text=text,
                parse_mode=parse_mode,
                reply_markup=reply_markup,
                disable_notification=disable_notification
            )
            return True
        except Exception as e:
            logger.error(f"❌ Failed to send message to {chat_id}: {e}")
            return False
    
    async def send_photo(
        self,
        chat_id: int,
        photo: bytes,
        caption: str = "",
        parse_mode: str = ParseMode.HTML,
        reply_markup: Optional[InlineKeyboardMarkup] = None
    ) -> bool:
        """Send photo with caption"""
        try:
            from telegram import InputFile
            import io
            
            photo_file = InputFile(io.BytesIO(photo), filename="chart.png")
            await self.bot.send_photo(
                chat_id=chat_id,
                photo=photo_file,
                caption=caption,
                parse_mode=parse_mode,
                reply_markup=reply_markup
            )
            return True
        except Exception as e:
            logger.error(f"❌ Failed to send photo to {chat_id}: {e}")
            return False
    
    async def send_document(
        self,
        chat_id: int,
        document: bytes,
        filename: str,
        caption: str = ""
    ) -> bool:
        """Send document"""
        try:
            from telegram import InputFile
            import io
            
            doc_file = InputFile(io.BytesIO(document), filename=filename)
            await self.bot.send_document(
                chat_id=chat_id,
                document=doc_file,
                caption=caption,
                parse_mode=ParseMode.HTML
            )
            return True
        except Exception as e:
            logger.error(f"❌ Failed to send document to {chat_id}: {e}")
            return False
    
    async def send_trade_alert(
        self,
        chat_id: int,
        trade_data: Dict[str, Any],
        chart_image: Optional[bytes] = None
    ) -> bool:
        """Send new trade alert"""
        message = MessageTemplates.new_trade(trade_data)
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("📊 التفاصيل", callback_data=f"trade_details_{trade_data['id']}"),
                InlineKeyboardButton("❌ إغلاق", callback_data=f"close_trade_{trade_data['id']}")
            ]
        ])
        
        if chart_image:
            return await self.send_photo(
                chat_id=chat_id,
                photo=chart_image,
                caption=message,
                reply_markup=keyboard
            )
        else:
            return await self.send_message(
                chat_id=chat_id,
                text=message,
                reply_markup=keyboard
            )
    
    async def send_trade_close_alert(
        self,
        chat_id: int,
        trade_data: Dict[str, Any],
        pnl: float,
        pnl_percent: float
    ) -> bool:
        """Send trade close alert"""
        message = MessageTemplates.trade_closed(trade_data, pnl, pnl_percent)
        return await self.send_message(chat_id=chat_id, text=message)
    
    async def send_daily_summary(
        self,
        chat_id: int,
        summary_data: Dict[str, Any]
    ) -> bool:
        """Send daily P&L summary"""
        message = MessageTemplates.daily_summary(summary_data)
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("📈 تقرير أسبوعي", callback_data="weekly_report"),
                InlineKeyboardButton("⚙️ الإعدادات", callback_data="settings")
            ]
        ])
        return await self.send_message(
            chat_id=chat_id,
            text=message,
            reply_markup=keyboard
        )
    
    async def send_risk_alert(
        self,
        chat_id: int,
        alert_type: str,
        data: Dict[str, Any]
    ) -> bool:
        """Send risk alert"""
        message = MessageTemplates.risk_alert(alert_type, data)
        return await self.send_message(
            chat_id=chat_id,
            text=message,
            disable_notification=False  # Always notify for risks
        )
    
    async def send_guardian_update(
        self,
        chat_id: int,
        update_type: str,
        data: Dict[str, Any]
    ) -> bool:
        """Send AI Guardian update"""
        message = MessageTemplates.guardian_update(update_type, data)
        return await self.send_message(chat_id=chat_id, text=message)
    
    async def broadcast_message(
        self,
        chat_ids: List[int],
        text: str,
        parse_mode: str = ParseMode.HTML
    ) -> Dict[int, bool]:
        """Broadcast message to multiple users"""
        results = {}
        for chat_id in chat_ids:
            results[chat_id] = await self.send_message(
                chat_id=chat_id,
                text=text,
                parse_mode=parse_mode
            )
        return results


# Global bot instance
telegram_bot = TelegramBot()
