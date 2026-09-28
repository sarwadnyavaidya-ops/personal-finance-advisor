from datetime import datetime, date
from math import ceil
from app.extensions import db


class ExpenseCategory(db.Model):
    __tablename__ = "expense_categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    type = db.Column(db.String(50), default="Discretionary", nullable=False)  # Essential, Discretionary, Debt/Savings, Other
    description = db.Column(db.String(255), nullable=True)
    is_default = db.Column(db.Boolean, default=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=True)

    # Relationships
    expenses = db.relationship("Expense", backref="category", lazy="dynamic")
    budgets = db.relationship("Budget", backref="category", lazy="dynamic")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "description": self.description,
            "is_default": self.is_default,
            "user_id": self.user_id
        }

    def __repr__(self):
        return f"<ExpenseCategory {self.name}>"


class Income(db.Model):
    __tablename__ = "incomes"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    amount = db.Column(db.Float, nullable=False)
    source = db.Column(db.String(80), nullable=False)  # Salary, Freelance, Business, Scholarship, Allowance, Investment, Other
    date = db.Column(db.Date, nullable=False, default=date.today, index=True)
    description = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "amount": self.amount,
            "source": self.source,
            "date": self.date.isoformat() if self.date else None,
            "description": self.description or "",
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

    def __repr__(self):
        return f"<Income {self.source}: {self.amount}>"


class Expense(db.Model):
    __tablename__ = "expenses"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    category_id = db.Column(db.Integer, db.ForeignKey("expense_categories.id"), nullable=False, index=True)
    amount = db.Column(db.Float, nullable=False)
    date = db.Column(db.Date, nullable=False, default=date.today, index=True)
    description = db.Column(db.String(255), nullable=True)
    payment_method = db.Column(db.String(50), default="Debit Card", nullable=False)  # Cash, Credit Card, Debit Card, Bank Transfer, UPI, Other
    is_recurring = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "category_id": self.category_id,
            "category_name": self.category.name if self.category else "Uncategorized",
            "category_type": self.category.type if self.category else "Other",
            "amount": self.amount,
            "date": self.date.isoformat() if self.date else None,
            "description": self.description or "",
            "payment_method": self.payment_method,
            "is_recurring": self.is_recurring,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

    def __repr__(self):
        return f"<Expense {self.category_id}: {self.amount}>"


class Budget(db.Model):
    __tablename__ = "budgets"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    category_id = db.Column(db.Integer, db.ForeignKey("expense_categories.id"), nullable=True, index=True)
    amount = db.Column(db.Float, nullable=False)
    month = db.Column(db.Integer, nullable=False)  # 1-12
    year = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "category_id": self.category_id,
            "category_name": self.category.name if self.category else "Overall Monthly Budget",
            "amount": self.amount,
            "month": self.month,
            "year": self.year,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

    def __repr__(self):
        return f"<Budget {self.category_id or 'Overall'} {self.month}/{self.year}: {self.amount}>"


class Savings(db.Model):
    __tablename__ = "savings"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    amount = db.Column(db.Float, nullable=False)
    date = db.Column(db.Date, nullable=False, default=date.today, index=True)
    source = db.Column(db.String(80), default="Savings Deposit", nullable=False)  # Savings Deposit, High-Yield Savings, Investment, Emergency Fund, Cash Savings, Other
    description = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "amount": self.amount,
            "date": self.date.isoformat() if self.date else None,
            "source": self.source,
            "description": self.description or "",
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

    def __repr__(self):
        return f"<Savings {self.source}: {self.amount}>"


class FinancialGoal(db.Model):
    __tablename__ = "financial_goals"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = db.Column(db.String(120), nullable=False)  # Laptop, Education, Travel, Emergency Fund, Vehicle, House, Investment, Other
    target_amount = db.Column(db.Float, nullable=False)
    current_amount = db.Column(db.Float, default=0.0, nullable=False)
    target_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(30), default="In Progress", nullable=False)  # In Progress, Achieved, On Hold
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    @property
    def remaining_amount(self) -> float:
        return max(0.0, self.target_amount - self.current_amount)

    @property
    def percentage_complete(self) -> float:
        if self.target_amount <= 0:
            return 100.0
        pct = (self.current_amount / self.target_amount) * 100.0
        return min(100.0, round(pct, 1))

    @property
    def required_monthly_saving(self) -> float:
        if self.current_amount >= self.target_amount:
            return 0.0
        today = date.today()
        if not self.target_date or self.target_date <= today:
            return self.remaining_amount
        
        # Calculate remaining months
        diff_years = self.target_date.year - today.year
        diff_months = self.target_date.month - today.month + (diff_years * 12)
        # If target day is earlier in month, count partial
        if self.target_date.day < today.day and diff_months > 0:
            diff_months -= 1
        months_left = max(1, diff_months)
        return round(self.remaining_amount / months_left, 2)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "target_amount": self.target_amount,
            "current_amount": self.current_amount,
            "target_date": self.target_date.isoformat() if self.target_date else None,
            "status": self.status,
            "remaining_amount": self.remaining_amount,
            "percentage_complete": self.percentage_complete,
            "required_monthly_saving": self.required_monthly_saving,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

    def __repr__(self):
        return f"<FinancialGoal {self.name}: {self.current_amount}/{self.target_amount}>"


class AIRecommendation(db.Model):
    __tablename__ = "ai_recommendations"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    recommendation_type = db.Column(db.String(50), nullable=False)  # Budget, Savings, Cost-Optimization, Emergency-Fund, Spending-Alert, Financial-Health
    content = db.Column(db.Text, nullable=False)
    key_metrics = db.Column(db.Text, nullable=True)  # JSON or comma-separated summary
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "recommendation_type": self.recommendation_type,
            "content": self.content,
            "key_metrics": self.key_metrics,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

    def __repr__(self):
        return f"<AIRecommendation {self.recommendation_type} for User {self.user_id}>"


class MonthlyReport(db.Model):
    __tablename__ = "monthly_reports"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    month = db.Column(db.Integer, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    total_income = db.Column(db.Float, default=0.0, nullable=False)
    total_expense = db.Column(db.Float, default=0.0, nullable=False)
    total_savings = db.Column(db.Float, default=0.0, nullable=False)
    report_content = db.Column(db.Text, nullable=True)  # Markdown or JSON structured summary
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "month": self.month,
            "year": self.year,
            "total_income": self.total_income,
            "total_expense": self.total_expense,
            "total_savings": self.total_savings,
            "net_cashflow": round(self.total_income - self.total_expense, 2),
            "report_content": self.report_content,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

    def __repr__(self):
        return f"<MonthlyReport {self.month}/{self.year} for User {self.user_id}>"


class FinancialAlert(db.Model):
    __tablename__ = "financial_alerts"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    type = db.Column(db.String(80), nullable=False)  # Budget Exceeded, Rapid Spending, Low Savings, Discretionary Alert, Emergency Fund Notice
    message = db.Column(db.String(255), nullable=False)
    severity = db.Column(db.String(20), default="warning", nullable=False)  # info, warning, danger
    is_read = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "type": self.type,
            "message": self.message,
            "severity": self.severity,
            "is_read": self.is_read,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

    def __repr__(self):
        return f"<FinancialAlert {self.severity}: {self.message[:30]}>"


class ChatMessage(db.Model):
    __tablename__ = "chat_messages"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    role = db.Column(db.String(20), nullable=False)  # user, assistant
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "role": self.role,
            "content": self.content,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

    def __repr__(self):
        return f"<ChatMessage {self.role}: {self.content[:20]}...>"
