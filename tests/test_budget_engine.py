from datetime import date
from app.extensions import db
from app.models.financial import Budget, Expense, ExpenseCategory, FinancialAlert
from app.services.finance_service import FinanceService
from app.services.alert_service import AlertService
from app.models.user import User


def test_budget_calculations_and_alerts(client, user_a, auth, app):
    auth.login("alice@example.com", "password123")
    today = date.today()

    with app.app_context():
        food_cat = ExpenseCategory.query.filter_by(name="Food", is_default=True).first()
        food_cat_id = food_cat.id

        # 1. Set Food category budget of $400 for current month
        budget = Budget(
            user_id=user_a,
            category_id=food_cat_id,
            amount=400.0,
            month=today.month,
            year=today.year
        )
        db.session.add(budget)

        # 2. Add Expense of $480 in Food (Exceeds $400 budget by $80)
        exp = Expense(
            user_id=user_a,
            category_id=food_cat_id,
            amount=480.0,
            date=today,
            description="Exceeding dinners",
            payment_method="Credit Card"
        )
        db.session.add(exp)
        db.session.commit()

        # 3. Check FinanceService budget status
        b_status = FinanceService.get_budget_status(user_a, today.year, today.month)
        assert len(b_status["category_budgets"]) == 1
        food_budget = b_status["category_budgets"][0]
        assert food_budget["is_overspent"] is True
        assert food_budget["overspent_amount"] == 80.0
        assert food_budget["utilization_percentage"] == 120.0
        assert any("exceeded your monthly budget by 80.00" in w for w in b_status["warnings"])

        # 4. Trigger AlertService and verify alert creation
        user = db.session.get(User, user_a)
        AlertService.generate_alerts_for_user(user, today.year, today.month)

        alert = FinancialAlert.query.filter_by(
            user_id=user_a,
            type="Budget Exceeded"
        ).first()
        assert alert is not None
        assert alert.severity == "danger"
        assert "Food budget exceeded by" in alert.message
