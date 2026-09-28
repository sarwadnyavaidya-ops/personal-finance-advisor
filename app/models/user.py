from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db, login_manager


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    preferred_currency = db.Column(db.String(10), default="USD", nullable=False)
    monthly_income = db.Column(db.Float, default=0.0, nullable=False)
    monthly_savings_target = db.Column(db.Float, default=0.0, nullable=False)
    emergency_fund_target = db.Column(db.Float, default=0.0, nullable=False)
    financial_goals_summary = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    incomes = db.relationship("Income", backref="user", lazy="dynamic", cascade="all, delete-orphan")
    expenses = db.relationship("Expense", backref="user", lazy="dynamic", cascade="all, delete-orphan")
    budgets = db.relationship("Budget", backref="user", lazy="dynamic", cascade="all, delete-orphan")
    savings_records = db.relationship("Savings", backref="user", lazy="dynamic", cascade="all, delete-orphan")
    financial_goals = db.relationship("FinancialGoal", backref="user", lazy="dynamic", cascade="all, delete-orphan")
    ai_recommendations = db.relationship("AIRecommendation", backref="user", lazy="dynamic", cascade="all, delete-orphan")
    monthly_reports = db.relationship("MonthlyReport", backref="user", lazy="dynamic", cascade="all, delete-orphan")
    financial_alerts = db.relationship("FinancialAlert", backref="user", lazy="dynamic", cascade="all, delete-orphan")
    chat_messages = db.relationship("ChatMessage", backref="user", lazy="dynamic", cascade="all, delete-orphan")

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    @property
    def currency_symbol(self) -> str:
        symbols = {
            "USD": "$",
            "INR": "₹",
            "EUR": "€",
            "GBP": "£",
            "CAD": "CA$",
            "AUD": "A$",
            "JPY": "¥",
            "SGD": "S$"
        }
        return symbols.get(self.preferred_currency, "$")

    def to_dict(self):
        return {
            "id": self.id,
            "full_name": self.full_name,
            "email": self.email,
            "preferred_currency": self.preferred_currency,
            "currency_symbol": self.currency_symbol,
            "monthly_income": self.monthly_income,
            "monthly_savings_target": self.monthly_savings_target,
            "emergency_fund_target": self.emergency_fund_target,
            "financial_goals_summary": self.financial_goals_summary,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

    def __repr__(self):
        return f"<User {self.email}>"


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))
