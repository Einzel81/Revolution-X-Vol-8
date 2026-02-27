"""
Telegram Bot Command & Callback Handlers
"""
import logging
from typing import Dict, Any
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from app.core.database import get_db
from app.models.user import User
from app.models.telegram_user import TelegramUser
from app.services.trading_service import TradingService
from app.services.user_service import UserService
from app.telegram.messages import MessageTemplates

logger = logging.getLogger(__name__)


class CommandHandlers:
    """Telegram command handlers"""
    
    @staticmethod
    async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user = update.effective_user
        chat_id = update.effective_chat.id
        
        welcome_message = f"""
🚀 <b>مرحباً بك في Revolution X!</b>
Welcome to Revolution X!

👤 <b>المستخدم:</b> {user.first_name}
🆔 <b>Chat ID:</b> <code>{chat_id}</code>

📌 <b>الأوامر المتاحة:</b>
/start - بدء البوت
/help - المساعدة
/status - حالة النظام
/positions - الصفقات المفتوحة
/profit - الأرباح
/balance - الرصيد
/daily - ملخص يومي
/weekly - تقرير أسبوعي
/settings - الإعدادات
/connect - ربط الحساب
/alerts - إدارة التنبيهات
/guardian - حالة AI Guardian

🔗 <b>لربط حسابك:</b>
استخدم الأمر /connect [your_api_key]
        """
        
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🔗 ربط الحساب", callback_data="connect_account"),
                InlineKeyboardButton("📊 الحالة", callback_data="system_status")
            ],
            [
                InlineKeyboardButton("❓ المساعدة", callback_data="help"),
                InlineKeyboardButton("⚙️ الإعدادات", callback_data="settings")
            ]
        ])
        
        await update.message.reply_text(
            welcome_message,
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard
        )
    
    @staticmethod
    async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_text = """
📚 <b>دليل استخدام البوت:</b>

<b>🎯 الأوامر الأساسية:</b>
/status - عرض حالة النظام والاتصال
/positions - قائمة الصفقات المفتوحة
/profit - إجمالي الأرباح والخسائر
/balance - رصيد الحساب المتاح

<b>📊 التقارير:</b>
/daily - ملخص الأداء اليومي
/weekly - تقرير الأداء الأسبوعي

<b>⚙️ الإدارة:</b>
/settings - إعدادات التنبيهات
/alerts - تفعيل/تعطيل التنبيهات
/connect - ربط بحساب Revolution X
/disconnect - فصل الربط

<b>🤖 AI Guardian:</b>
/guardian - عرض حالة الحارس الذكي

<b>💡 نصائح:</b>
• استخدم الأزرار للتنقل السريع
• يمكنك استلام تنبيهات فورية للصفقات
• فعّل "ساعات الصمت" من الإعدادات
        """
        await update.message.reply_text(help_text, parse_mode=ParseMode.HTML)
    
    @staticmethod
    async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command"""
        chat_id = update.effective_chat.id
        
        # Check if user is connected
        async with get_db() as db:
            telegram_user = await db.query(TelegramUser).filter(
                TelegramUser.chat_id == chat_id
            ).first()
            
            if not telegram_user or not telegram_user.is_active:
                await update.message.reply_text(
                    "⚠️ <b>غير متصل</b>\nلم يتم ربط حسابك بعد.\n\n"
                    "استخدم /connect [api_key] للربط",
                    parse_mode=ParseMode.HTML
                )
                return
        
        # Get system status
        status_text = f"""
✅ <b>النظام يعمل بكفاءة</b>

📡 <b>حالة الاتصال:</b> متصل
🤖 <b>AI Guardian:</b> نشط
⚡ <b>وقت الاستجابة:</b> 45ms

🕐 <b>آخر تحديث:</b> الآن
        """
        
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🔄 تحديث", callback_data="refresh_status"),
                InlineKeyboardButton("📊 التفاصيل", callback_data="detailed_status")
            ]
        ])
        
        await update.message.reply_text(
            status_text,
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard
        )
    
    @staticmethod
    async def positions(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /positions command"""
        chat_id = update.effective_chat.id
        
        # Mock data - replace with actual service call
        positions = [
            {"symbol": "BTCUSDT", "side": "LONG", "entry": 45000, "current": 46500, "pnl": 1500, "size": 0.5},
            {"symbol": "ETHUSDT", "side": "SHORT", "entry": 3000, "current": 2950, "pnl": 100, "size": 2}
        ]
        
        if not positions:
            await update.message.reply_text("📭 <b>لا توجد صفقات مفتوحة</b>", parse_mode=ParseMode.HTML)
            return
        
        message = "📊 <b>الصفقات المفتوحة:</b>\n\n"
        total_pnl = 0
        
        for pos in positions:
            emoji = "🟢" if pos['pnl'] >= 0 else "🔴"
            total_pnl += pos['pnl']
            message += f"""
{emoji} <b>{pos['symbol']}</b> | {pos['side']}
💰 الدخول: ${pos['entry']:,.2f}
📈 الحالي: ${pos['current']:,.2f}
💵 الربح: ${pos['pnl']:,.2f}
📦 الحجم: {pos['size']}
───────────────
"""
        
        message += f"\n<b>إجمالي الربح:</b> ${total_pnl:,.2f}"
        
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🔄 تحديث", callback_data="refresh_positions"),
                InlineKeyboardButton("❌ إغلاق الكل", callback_data="close_all")
            ]
        ])
        
        await update.message.reply_text(
            message,
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard
        )
    
    @staticmethod
    async def profit(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /profit command"""
        # Mock data
        profit_data = {
            "today": 1250.50,
            "week": 8750.25,
            "month": 32400.80,
            "total": 156780.45,
            "win_rate": 68.5,
            "trades_count": 156
        }
        
        message = f"""
💰 <b>تقرير الأرباح</b>

📅 <b>اليوم:</b> ${profit_data['today']:,.2f}
📆 <b>هذا الأسبوع:</b> ${profit_data['week']:,.2f}
📊 <b>هذا الشهر:</b> ${profit_data['month']:,.2f}
💎 <b>الإجمالي:</b> ${profit_data['total']:,.2f}

📈 <b>نسبة الفوز:</b> {profit_data['win_rate']}%
🎯 <b>عدد الصفقات:</b> {profit_data['trades_count']}
        """
        
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("📊 رسم بياني", callback_data="profit_chart"),
                InlineKeyboardButton("📋 تفاصيل", callback_data="profit_details")
            ]
        ])
        
        await update.message.reply_text(
            message,
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard
        )
    
    @staticmethod
    async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /balance command"""
        balance_data = {
            "total": 50000.00,
            "available": 35000.00,
            "in_positions": 15000.00,
            "margin_used": 30.0
        }
        
        message = f"""
💳 <b>رصيد الحساب</b>

💰 <b>الإجمالي:</b> ${balance_data['total']:,.2f}
✅ <b>المتاح:</b> ${balance_data['available']:,.2f}
🔒 <b>في الصفقات:</b> ${balance_data['in_positions']:,.2f}
📊 <b>الهامش المستخدم:</b> {balance_data['margin_used']}%
        """
        
        await update.message.reply_text(message, parse_mode=ParseMode.HTML)
    
    @staticmethod
    async def daily_summary(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /daily command"""
        summary_data = {
            "date": "2024-01-20",
            "trades": 12,
            "wins": 8,
            "losses": 4,
            "pnl": 1250.50,
            "win_rate": 66.7,
            "best_trade": 450.00,
            "worst_trade": -120.00
        }
        
        message = MessageTemplates.daily_summary(summary_data)
        await update.message.reply_text(message, parse_mode=ParseMode.HTML)
    
    @staticmethod
    async def weekly_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /weekly command"""
        weekly_data = {
            "week": "الأسبوع 3 - يناير 2024",
            "total_pnl": 8750.25,
            "trades": 45,
            "win_rate": 68.5,
            "best_day": "الثلاثاء (+$2,340)",
            "worst_day": "الخميس (-$450)"
        }
        
        message = f"""
📊 <b>التقرير الأسبوعي</b>
<b>{weekly_data['week']}</b>

💰 <b>الربح الإجمالي:</b> ${weekly_data['total_pnl']:,.2f}
🎯 <b>عدد الصفقات:</b> {weekly_data['trades']}
📈 <b>نسبة الفوز:</b> {weekly_data['win_rate']}%

🏆 <b>أفضل يوم:</b> {weekly_data['best_day']}
⚠️ <b>أسوأ يوم:</b> {weekly_data['worst_day']}
        """
        
        await update.message.reply_text(message, parse_mode=ParseMode.HTML)
    
    @staticmethod
    async def settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /settings command"""
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🔔 التنبيهات", callback_data="alert_settings"),
                InlineKeyboardButton("🌐 اللغة", callback_data="language_settings")
            ],
            [
                InlineKeyboardButton("⏰ ساعات الصمت", callback_data="quiet_hours"),
                InlineKeyboardButton("📊 التقارير", callback_data="report_settings")
            ],
            [
                InlineKeyboardButton("🔙 رجوع", callback_data="main_menu")
            ]
        ])
        
        await update.message.reply_text(
            "⚙️ <b>الإعدادات</b>\nاختر الإعداد الذي تريد تعديله:",
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard
        )
    
    @staticmethod
    async def connect_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /connect command"""
        if not context.args:
            await update.message.reply_text(
                "⚠️ <b>يرجى إدخال مفتاح API</b>\n\n"
                "الاستخدام: <code>/connect YOUR_API_KEY</code>\n\n"
                "يمكنك الحصول على مفتاح API من لوحة التحكم",
                parse_mode=ParseMode.HTML
            )
            return
        
        api_key = context.args[0]
        chat_id = update.effective_chat.id
        user = update.effective_user
        
        # Here you would validate API key and link accounts
        # For now, show success message
        
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ تأكيد", callback_data=f"confirm_connect_{api_key}"),
                InlineKeyboardButton("❌ إلغاء", callback_data="cancel_connect")
            ]
        ])
        
        await update.message.reply_text(
            f"🔗 <b>ربط الحساب</b>\n\n"
            f"مفتاح API: <code>{api_key[:10]}...</code>\n"
            f"المستخدم: {user.first_name}\n\n"
            f"هل تريد ربط هذا الحساب؟",
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard
        )
    
    @staticmethod
    async def disconnect_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /disconnect command"""
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ نعم، فصل الربط", callback_data="confirm_disconnect"),
                InlineKeyboardButton("❌ إلغاء", callback_data="cancel_disconnect")
            ]
        ])
        
        await update.message.reply_text(
            "⚠️ <b>فصل الربط</b>\n\n"
            "هل أنت متأكد من فصل ربط Telegram بحساب Revolution X؟\n\n"
            "لن تتلقى أي تنبيهات بعد الفصل.",
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard
        )
    
    @staticmethod
    async def manage_alerts(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /alerts command"""
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🟢 صفقات جديدة", callback_data="toggle_new_trades"),
                InlineKeyboardButton("🔴 إغلاق الصفقات", callback_data="toggle_close_trades")
            ],
            [
                InlineKeyboardButton("⚠️ تنبيهات المخاطر", callback_data="toggle_risk_alerts"),
                InlineKeyboardButton("🤖 AI Guardian", callback_data="toggle_guardian")
            ],
            [
                InlineKeyboardButton("📊 الملخص اليومي", callback_data="toggle_daily_summary"),
                InlineKeyboardButton("📈 التقارير", callback_data="toggle_reports")
            ]
        ])
        
        await update.message.reply_text(
            "🔔 <b>إدارة التنبيهات</b>\n\n"
            "اختر نوع التنبيه لتفعيله/تعطيله:",
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard
        )
    
    @staticmethod
    async def guardian_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /guardian command"""
        guardian_data = {
            "status": "نشط",
            "mode": "محافظ",
            "optimizations": 12,
            "last_update": "منذ 2 ساعة",
            "performance_boost": "+15%"
        }
        
        message = f"""
🤖 <b>AI Guardian - الحارس الذكي</b>

📊 <b>الحالة:</b> {guardian_data['status']}
🎯 <b>الوضع:</b> {guardian_data['mode']}
⚡ <b>التحسينات:</b> {guardian_data['optimizations']}
🕐 <b>آخر تحديث:</b> {guardian_data['last_update']}
📈 <b>تحسين الأداء:</b> {guardian_data['performance_boost']}

<b>الميزات النشطة:</b>
✅ تحسين تلقائي للاستراتيجيات
✅ إدارة المخاطر الذكية
✅ اكتشاف أنماط السوق
✅ تعديلات فورية للمعلمات
        """
        
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("⚙️ الإعدادات", callback_data="guardian_settings"),
                InlineKeyboardButton("📊 التقرير", callback_data="guardian_report")
            ]
        ])
        
        await update.message.reply_text(
            message,
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard
        )
    
    @staticmethod
    async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle regular text messages"""
        text = update.message.text
        
        # Simple response for non-command messages
        if "مرحبا" in text or "hello" in text.lower():
            await update.message.reply_text(
                "👋 أهلاً بك! كيف يمكنني مساعدتك اليوم؟\n"
                "استخدم /help لعرض قائمة الأوامر"
            )
        else:
            await update.message.reply_text(
                "🤔 لم أفهم طلبك.\n"
                "استخدم /help لعرض الأوامر المتاحة\n"
                "أو تواصل مع الدعم الفني"
            )


class CallbackHandlers:
    """Callback query handlers for inline keyboards"""
    
    @staticmethod
    async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle all callback queries"""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        
        # Main menu navigation
        if data == "main_menu":
            await CommandHandlers.start(update, context)
        
        elif data == "help":
            await CommandHandlers.help(update, context)
        
        elif data == "settings":
            await CommandHandlers.settings(update, context)
        
        elif data == "system_status":
            await CommandHandlers.status(update, context)
        
        # Trade actions
        elif data.startswith("trade_details_"):
            trade_id = data.replace("trade_details_", "")
            await query.edit_message_text(
                f"📊 <b>تفاصيل الصفقة {trade_id}</b>\n\n"
                f"جاري تحميل التفاصيل...",
                parse_mode=ParseMode.HTML
            )
        
        elif data.startswith("close_trade_"):
            trade_id = data.replace("close_trade_", "")
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("✅ تأكيد", callback_data=f"confirm_close_{trade_id}"),
                    InlineKeyboardButton("❌ إلغاء", callback_data="cancel_close")
                ]
            ])
            await query.edit_message_reply_markup(reply_markup=keyboard)
        
        # Alert toggles
        elif data.startswith("toggle_"):
            alert_type = data.replace("toggle_", "")
            await query.edit_message_text(
                f"✅ تم {'تفعيل' if True else 'تعطيل'} تنبيهات {alert_type}",
                parse_mode=ParseMode.HTML
            )
        
        # Account connection
        elif data == "connect_account":
            await query.edit_message_text(
                "🔗 <b>ربط الحساب</b>\n\n"
                "أرسل مفتاح API الخاص بك باستخدام الأمر:\n"
                "<code>/connect YOUR_API_KEY</code>",
                parse_mode=ParseMode.HTML
            )
        
        # Refresh actions
        elif data == "refresh_status":
            await CommandHandlers.status(update, context)
        elif data == "refresh_positions":
            await CommandHandlers.positions(update, context)
        
        # Guardian
        elif data == "guardian_settings":
            await query.edit_message_text(
                "⚙️ <b>إعدادات AI Guardian</b>\n\n"
                "الوضع: محافظ/عدواني/متوازن\n"
                "التعلم التلقائي: مفعل\n"
                "إشعارات التحسين: مفعلة",
                parse_mode=ParseMode.HTML
            )
        
        else:
            await query.edit_message_text(
                "⚠️ هذا الخيار غير متاح حالياً",
                parse_mode=ParseMode.HTML
            )
