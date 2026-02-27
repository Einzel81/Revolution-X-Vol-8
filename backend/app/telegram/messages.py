"""
Telegram Message Templates
"""
from datetime import datetime
from typing import Dict, Any, Optional


class MessageTemplates:
    """Pre-formatted message templates"""
    
    @staticmethod
    def new_trade(trade_data: Dict[str, Any]) -> str:
        """Template for new trade alert"""
        emoji = "🟢" if trade_data.get('side') == 'LONG' else "🔴"
        
        return f"""
{emoji} <b>صفقة جديدة - New Trade</b>

💎 <b>الزوج:</b> {trade_data.get('symbol', 'N/A')}
📊 <b>الاتجاه:</b> {trade_data.get('side', 'N/A')}
💰 <b>السعر:</b> ${trade_data.get('entry_price', 0):,.2f}
📦 <b>الحجم:</b> {trade_data.get('size', 0)}
🎯 <b>الرافعة:</b> {trade_data.get('leverage', 1)}x

🟢 <b>TP:</b> ${trade_data.get('take_profit', 0):,.2f}
🔴 <b>SL:</b> ${trade_data.get('stop_loss', 0):,.2f}

🤖 <b>الاستراتيجية:</b> {trade_data.get('strategy', 'AI Guardian')}
⏰ <b>الوقت:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
🆔 <b>ID:</b> <code>{trade_data.get('id', 'N/A')}</code>
        """
    
    @staticmethod
    def trade_closed(trade_data: Dict[str, Any], pnl: float, pnl_percent: float) -> str:
        """Template for trade close alert"""
        is_profit = pnl >= 0
        emoji = "✅" if is_profit else "❌"
        pnl_emoji = "🟢" if is_profit else "🔴"
        
        return f"""
{emoji} <b>صفقة مغلقة - Trade Closed</b>

💎 <b>الزوج:</b> {trade_data.get('symbol', 'N/A')}
📊 <b>الاتجاه:</b> {trade_data.get('side', 'N/A')}

💰 <b>سعر الدخول:</b> ${trade_data.get('entry_price', 0):,.2f}
🏁 <b>سعر الخروج:</b> ${trade_data.get('exit_price', 0):,.2f}

{pnl_emoji} <b>الربح/الخسارة:</b> ${pnl:,.2f} ({pnl_percent:+.2f}%)
⏱️ <b>مدة الصفقة:</b> {trade_data.get('duration', 'N/A')}

🤖 <b>الاستراتيجية:</b> {trade_data.get('strategy', 'AI Guardian')}
🎯 <b>سبب الإغلاق:</b> {trade_data.get('close_reason', 'Manual')}
⏰ <b>الوقت:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
    
    @staticmethod
    def daily_summary(data: Dict[str, Any]) -> str:
        """Template for daily summary"""
        pnl_emoji = "🟢" if data.get('pnl', 0) >= 0 else "🔴"
        
        return f"""
📊 <b>الملخص اليومي - Daily Summary</b>
<b>{data.get('date', datetime.now().strftime('%Y-%m-%d'))}</b>

🎯 <b>إجمالي الصفقات:</b> {data.get('trades', 0)}
🏆 <b>الصفقات الرابحة:</b> {data.get('wins', 0)}
❌ <b>الصفقات الخاسرة:</b> {data.get('losses', 0)}
📈 <b>نسبة الفوز:</b> {data.get('win_rate', 0)}%

{pnl_emoji} <b>صافي الربح:</b> ${data.get('pnl', 0):,.2f}
💎 <b>أفضل صفقة:</b> ${data.get('best_trade', 0):,.2f}
⚠️ <b>أسوأ صفقة:</b> ${data.get('worst_trade', 0):,.2f}

📊 <b>الحالة:</b> {'ربحية' if data.get('pnl', 0) >= 0 else 'خاسرة'}
        """
    
    @staticmethod
    def risk_alert(alert_type: str, data: Dict[str, Any]) -> str:
        """Template for risk alerts"""
        templates = {
            'drawdown': f"""
🚨 <b>تنبيه مخاطر عالي - High Risk Alert</b>

⚠️ <b>نوع التنبيه:</b> انخفاض حاد في رصيد الحساب
📉 <b>نسبة الانخفاض:</b> {data.get('drawdown_percent', 0)}%
💰 <b>الخسارة:</b> ${data.get('loss_amount', 0):,.2f}

🔴 <b>الإجراء الموصى به:</b>
• مراجعة الصفقات المفتوحة
• تقليل حجم المراكز
• تفعيل وقف الخسارة

⏰ <b>الوقت:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            """,
            
            'consecutive_losses': f"""
⚠️ <b>تنبيه خسائر متتالية - Consecutive Losses</b>

🔴 <b>عدد الخسائر المتتالية:</b> {data.get('count', 0)}
📉 <b>إجمالي الخسارة:</b> ${data.get('total_loss', 0):,.2f}
🎯 <b>الاستراتيجية:</b> {data.get('strategy', 'N/A')}

💡 <b>توصية AI Guardian:</b>
• إيقاف التداول مؤقتاً
• مراجعة إعدادات الاستراتيجية
• تقليل حجم الصفقات 50%

⏰ <b>الوقت:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            """,
            
            'margin_call': f"""
🆘 <b>تنبيه هامش - Margin Warning</b>

⚠️ <b>الهامش المتاح:</b> {data.get('available_margin', 0)}%
🔴 <b>الهامش المستخدم:</b> {data.get('used_margin', 0)}%

🚨 <b>خطر التصفية!</b>

الإجراءات المطلوبة:
• إضافة رصيد للحساب
• إغلاق بعض المراكز
• تقليل الرافعة المالية

⏰ <b>الوقت:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            """,
            
            'volatility': f"""
⚡ <b>تنبيه تقلب عالي - High Volatility</b>

📊 <b>الزوج:</b> {data.get('symbol', 'N/A')}
⚡ <b>التقلب:</b> {data.get('volatility', 0)}%
📈 <b>التغير:</b> {data.get('change', 0):+.2f}%

💡 <b>نصيحة:</b>
• زيادة مسافة وقف الخسارة
• تقليل حجم الصفقات
• الانتباه للأخبار

⏰ <b>الوقت:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            """
        }
        
        return templates.get(alert_type, f"""
⚠️ <b>تنبيه - Alert</b>

<b>النوع:</b> {alert_type}
<b>البيانات:</b> {data}

⏰ <b>الوقت:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """)
    
    @staticmethod
    def guardian_update(update_type: str, data: Dict[str, Any]) -> str:
        """Template for AI Guardian updates"""
        templates = {
            'optimization': f"""
🤖 <b>AI Guardian - تحديث</b>

✅ <b>تم تطبيق تحسين جديد!</b>

📊 <b>الاستراتيجية:</b> {data.get('strategy', 'N/A')}
⚡ <b>نوع التحسين:</b> {data.get('optimization_type', 'N/A')}
📈 <b>التوقع:</b> {data.get('expected_improvement', 'N/A')}

🔧 <b>التغييرات:</b>
{data.get('changes', 'No details available')}

⏰ <b>الوقت:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            """,
            
            'parameter_change': f"""
🤖 <b>AI Guardian - تعديل معلمات</b>

⚙️ <b>تم تعديل المعلمات تلقائياً</b>

📊 <b>الاستراتيجية:</b> {data.get('strategy', 'N/A')}
🎯 <b>المعلم المعدل:</b> {data.get('parameter', 'N/A')}
📝 <b>القيمة القديمة:</b> {data.get('old_value', 'N/A')}
✅ <b>القيمة الجديدة:</b> {data.get('new_value', 'N/A')}

💡 <b>السبب:</b> {data.get('reason', 'Optimization')}

⏰ <b>الوقت:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            """,
            
            'performance_report': f"""
🤖 <b>AI Guardian - تقرير الأداء</b>

📈 <b>التحسن في الأداء:</b> {data.get('improvement', 'N/A')}
🎯 <b>الصفقات المحسنة:</b> {data.get('optimized_trades', 0)}
⚡ <b>معدل النجاح:</b> {data.get('success_rate', 0)}%

🏆 <b>أفضل تحسين:</b> {data.get('best_improvement', 'N/A')}
📊 <b>الاستراتيجيات النشطة:</b> {data.get('active_strategies', 0)}

⏰ <b>الوقت:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            """
        }
        
        return templates.get(update_type, f"""
🤖 <b>AI Guardian Update</b>

<b>النوع:</b> {update_type}
<b>البيانات:</b> {data}

⏰ <b>الوقت:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """)
    
    @staticmethod
    def partial_close(trade_data: Dict[str, Any], closed_percent: float, pnl: float) -> str:
        """Template for partial close notification"""
        return f"""
🔶 <b>إغلاق جزئي - Partial Close</b>

💎 <b>الزوج:</b> {trade_data.get('symbol', 'N/A')}
📊 <b>الاتجاه:</b> {trade_data.get('side', 'N/A')}

🔢 <b>نسبة الإغلاق:</b> {closed_percent}%
💰 <b>الربح المحقق:</b> ${pnl:,.2f}
📦 <b>الكمية المتبقية:</b> {trade_data.get('remaining_size', 0)}

⏰ <b>الوقت:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
    
    @staticmethod
    def price_alert(symbol: str, target_price: float, current_price: float, alert_type: str = 'above') -> str:
        """Template for price alert"""
        emoji = "🟢" if alert_type == 'above' else "🔴"
        direction = "أعلى" if alert_type == 'above' else "أقل"
        
        return f"""
🎯 <b>تنبيه سعر - Price Alert</b>

💎 <b>الزوج:</b> {symbol}
{emoji} <b>السعر الحالي:</b> ${current_price:,.2f}
🎯 <b>الهدف:</b> ${target_price:,.2f}
📈 <b>الاتجاه:</b> {direction} من الهدف

⏰ <b>الوقت:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
    
    @staticmethod
    def system_status(status: str, details: Dict[str, Any]) -> str:
        """Template for system status"""
        status_emoji = "🟢" if status == "operational" else "🔴" if status == "down" else "🟡"
        
        return f"""
🚀 <b>حالة النظام - System Status</b>

{status_emoji} <b>الحالة:</b> {status.upper()}

📡 <b>API:</b> {'✅ متصل' if details.get('api_connected') else '❌ غير متصل'}
🤖 <b>AI Guardian:</b> {'✅ نشط' if details.get('guardian_active') else '❌ غير نشط'}
💾 <b>قاعدة البيانات:</b> {'✅ متصلة' if details.get('db_connected') else '❌ غير متصلة'}
⚡ <b>وقت الاستجابة:</b> {details.get('latency', 'N/A')}ms

🕐 <b>آخر تحديث:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
    
    @staticmethod
    def welcome_connected(user_name: str) -> str:
        """Welcome message after connection"""
        return f"""
✅ <b>تم الربط بنجاح!</b>

👋 أهلاً بك، {user_name}!
تم ربط حسابك في Revolution X بنجاح.

🔔 <b>التنبيهات المفعلة:</b>
• صفقات جديدة ✅
• إغلاق الصفقات ✅
• تنبيهات المخاطر ✅
• ملخص يومي ✅

💡 <b>لإدارة التنبيهات:</b> استخدم /alerts
⚙️ <b>للإعدادات:</b> استخدم /settings

🚀 جاهز للتداول الذكي!
        """
