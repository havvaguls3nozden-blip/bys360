from .account_handlers import (
    account,
    account_change_password,
    account_change_photo,
    account_security_setup,
    enforce_first_login_security_flow,
    settings_page,
)
from .auth_handlers import forgot_password, login, logout, setup_admin
from .comparison_handlers import my_performance_comparison, team_performance_comparison_history
from .dashboard_handlers import dashboard, db_check
from .public_handlers import education_management, home, index, strategy_management

__all__ = [
    "account",
    "account_change_password",
    "account_change_photo",
    "account_security_setup",
    "dashboard",
    "db_check",
    "education_management",
    "enforce_first_login_security_flow",
    "forgot_password",
    "home",
    "index",
    "login",
    "logout",
    "my_performance_comparison",
    "settings_page",
    "setup_admin",
    "strategy_management",
    "team_performance_comparison_history",
]