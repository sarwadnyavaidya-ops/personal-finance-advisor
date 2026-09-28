from app.routes.auth import auth_bp
from app.routes.main import main_bp
from app.routes.income import income_bp
from app.routes.expense import expense_bp
from app.routes.budget import budget_bp
from app.routes.savings import savings_bp
from app.routes.goals import goals_bp
from app.routes.analysis import analysis_bp
from app.routes.advisor import advisor_bp
from app.routes.reports import reports_bp
from app.routes.alerts import alerts_bp
from app.routes.api import api_bp

__all__ = [
    "auth_bp",
    "main_bp",
    "income_bp",
    "expense_bp",
    "budget_bp",
    "savings_bp",
    "goals_bp",
    "analysis_bp",
    "advisor_bp",
    "reports_bp",
    "alerts_bp",
    "api_bp"
]
