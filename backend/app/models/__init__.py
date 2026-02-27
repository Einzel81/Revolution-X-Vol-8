# backend/app/models/__init__.py

# Import all models so SQLAlchemy Base knows about them before create_all()

from app.models.user import User  # noqa: F401
from app.models.trade import Trade  # noqa: F401
from app.models.trading_signal import TradingSignal  # noqa: F401
from app.models.execution_log import ExecutionLog  # noqa: F401

from app.models.alert import Alert  # noqa: F401
from app.models.notification import Notification  # noqa: F401
from app.models.telegram_user import TelegramUser  # noqa: F401