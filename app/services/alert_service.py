from datetime import date
from sqlalchemy import func, extract
from app.extensions import db
from app.models.financial import FinancialAlert, Expense, Budget, ExpenseCategory
from app.models.user import User


class AlertService:
    @staticmethod
    def generate_alerts_for_user(user: User, year: int, month: int):
        """Scans user financial activity and generates actionable financial alerts."""
        alerts_to_create = []

        # 1. Check Category Budgets
        budgets = Budget.query.filter_by(user_id=user.id, year=year, month=month).all()
        for b in budgets:
            if b.category_id is not None:
                spent = db.session.query(func.coalesce(func.sum(Expense.amount), 0.0)).filter(
                    Expense.user_id == user.id,
                    Expense.category_id == b.category_id,
                    extract("year", Expense.date) == year,
                    extract("month", Expense.date) == month
                ).scalar() or 0.0

                cat_name = b.category.name if b.category else "Category"
                if spent > b.amount:
                    over_amt = spent - b.amount
                    msg = f"{cat_name} budget exceeded by {user.currency_symbol}{over_amt:,.2f}."
                    alerts_to_create.append({
                        "type": "Budget Exceeded",
                        "message": msg,
                        "severity": "danger"
                    })
                elif spent >= (b.amount * 0.85):
                    pct = round((spent / b.amount) * 100, 1)
                    msg = f"{cat_name} budget is {pct}% utilized ({user.currency_symbol}{spent:,.2f} of {user.currency_symbol}{b.amount:,.2f})."
                    alerts_to_create.append({
                        "type": "Budget Warning",
                        "message": msg,
                        "severity": "warning"
                    })

        # 2. Check Overall Budget
        overall_budget = next((b for b in budgets if b.category_id is None), None)
        if overall_budget:
            total_spent = db.session.query(func.coalesce(func.sum(Expense.amount), 0.0)).filter(
                Expense.user_id == user.id,
                extract("year", Expense.date) == year,
                extract("month", Expense.date) == month
            ).scalar() or 0.0

            if total_spent > overall_budget.amount:
                over_amt = total_spent - overall_budget.amount
                alerts_to_create.append({
                    "type": "Budget Exceeded",
                    "message": f"Total monthly spending has exceeded overall budget by {user.currency_symbol}{over_amt:,.2f}.",
                    "severity": "danger"
                })

        # 3. Check for Unusual Single Expenses (> 25% of baseline monthly income or > 500)
        income_benchmark = user.monthly_income if user.monthly_income > 0 else 2000.0
        threshold = income_benchmark * 0.30
        large_expenses = Expense.query.filter(
            Expense.user_id == user.id,
            extract("year", Expense.date) == year,
            extract("month", Expense.date) == month,
            Expense.amount >= threshold
        ).all()

        for exp in large_expenses:
            cat_name = exp.category.name if exp.category else "Expense"
            msg = f"Large transaction flagged: {user.currency_symbol}{exp.amount:,.2f} on {cat_name} ('{exp.description or 'No note'}')."
            alerts_to_create.append({
                "type": "High Transaction",
                "message": msg,
                "severity": "info"
            })

        # 4. Check Savings Target vs Current Month Savings
        if user.monthly_savings_target > 0:
            from app.models.financial import Savings
            monthly_saved = db.session.query(func.coalesce(func.sum(Savings.amount), 0.0)).filter(
                Savings.user_id == user.id,
                extract("year", Savings.date) == year,
                extract("month", Savings.date) == month
            ).scalar() or 0.0

            today = date.today()
            if today.year == year and today.month == month and today.day >= 20 and monthly_saved < (user.monthly_savings_target * 0.5):
                alerts_to_create.append({
                    "type": "Low Savings",
                    "message": f"Monthly savings ({user.currency_symbol}{monthly_saved:,.2f}) are significantly behind target ({user.currency_symbol}{user.monthly_savings_target:,.2f}).",
                    "severity": "warning"
                })

        # Prevent duplicate identical messages created in last 7 days
        for item in alerts_to_create:
            existing = FinancialAlert.query.filter_by(
                user_id=user.id,
                type=item["type"],
                message=item["message"]
            ).first()

            if not existing:
                alert = FinancialAlert(
                    user_id=user.id,
                    type=item["type"],
                    message=item["message"],
                    severity=item["severity"],
                    is_read=False
                )
                db.session.add(alert)

        db.session.commit()
