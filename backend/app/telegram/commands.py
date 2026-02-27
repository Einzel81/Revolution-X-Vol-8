"""
Telegram Bot Commands Registry
"""
from enum import Enum
from typing import Dict, List


class BotCommands:
    """Available bot commands"""
    
    COMMANDS = {
        'start': {
            'command': '/start',
            'description': 'بدء البوت / Start the bot',
            'admin_only': False
        },
        'help': {
            'command': '/help',
            'description': 'المساعدة / Help',
            'admin_only': False
        },
        'status': {
            'command': '/status',
            'description': 'حالة النظام / System status',
            'admin_only': False
        },
        'positions': {
            'command': '/positions',
            'description': 'الصفقات المفتوحة / Open positions',
            'admin_only': False
        },
        'profit': {
            'command': '/profit',
            'description': 'الأرباح / Profits',
            'admin_only': False
        },
        'balance': {
            'command': '/balance',
            'description': 'الرصيد / Balance',
            'admin_only': False
        },
        'daily': {
            'command': '/daily',
            'description': 'ملخص يومي / Daily summary',
            'admin_only': False
        },
        'weekly': {
            'command': '/weekly',
            'description': 'تقرير أسبوعي / Weekly report',
            'admin_only': False
        },
        'settings': {
            'command': '/settings',
            'description': 'الإعدادات / Settings',
            'admin_only': False
        },
        'connect': {
            'command': '/connect',
            'description': 'ربط الحساب / Connect account',
            'admin_only': False
        },
        'disconnect': {
            'command': '/disconnect',
            'description': 'فصل الربط / Disconnect',
            'admin_only': False
        },
        'alerts': {
            'command': '/alerts',
            'description': 'إدارة التنبيهات / Manage alerts',
            'admin_only': False
        },
        'guardian': {
            'command': '/guardian',
            'description': 'حالة AI Guardian / AI Guardian status',
            'admin_only': False
        },
        'admin_broadcast': {
            'command': '/broadcast',
            'description': 'إرسال رسالة للجميع (أدمن فقط) / Broadcast (admin only)',
            'admin_only': True
        },
        'admin_stats': {
            'command': '/stats',
            'description': 'إحصائيات (أدمن فقط) / Statistics (admin only)',
            'admin_only': True
        }
    }
    
    @classmethod
    def get_command_list(cls, is_admin: bool = False) -> List[Dict[str, str]]:
        """Get list of commands for BotFather"""
        commands = []
        for key, value in cls.COMMANDS.items():
            if not value['admin_only'] or is_admin:
                commands.append({
                    'command': value['command'].replace('/', ''),
                    'description': value['description']
                })
        return commands
    
    @classmethod
    def get_command_description(cls, command: str) -> str:
        """Get description for specific command"""
        cmd = cls.COMMANDS.get(command.replace('/', ''), {})
        return cmd.get('description', 'No description available')
    
    @classmethod
    def is_admin_command(cls, command: str) -> bool:
        """Check if command is admin-only"""
        cmd = cls.COMMANDS.get(command.replace('/', ''), {})
        return cmd.get('admin_only', False)
