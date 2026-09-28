from datetime import date, timedelta
from app.extensions import db
from app.models.financial import Income, Expense, ExpenseCategory, Savings, FinancialGoal


def test_income_crud(client, user_a, auth, app):
    auth.login("alice@example.com", "password123")

    # 1. Add valid income
    resp = client.post(
        "/income/add",
        data={
            "amount": "4500.50",
            "source": "Salary",
            "date": "2026-09-01",
            "description": "Tech Corp Monthly Base"
        },
        follow_redirects=True
    )
    assert resp.status_code == 200
    assert b"Successfully recorded income" in resp.data

    with app.app_context():
        inc = Income.query.filter_by(user_id=user_a).first()
        assert inc is not None
        assert inc.amount == 4500.50
        assert inc.source == "Salary"
        inc_id = inc.id

    # 2. Reject negative amount
    resp_neg = client.post(
        "/income/add",
        data={"amount": "-100", "source": "Salary", "date": "2026-09-01"},
        follow_redirects=True
    )
    assert b"Income amount must be greater than zero" in resp_neg.data

    # 3. Edit income
    resp_edit = client.post(
        f"/income/edit/{inc_id}",
        data={
            "amount": "4800.00",
            "source": "Salary",
            "date": "2026-09-01",
            "description": "Updated Base"
        },
        follow_redirects=True
    )
    assert resp_edit.status_code == 200

    with app.app_context():
        updated_inc = db.session.get(Income, inc_id)
        assert updated_inc.amount == 4800.00

    # 4. Delete income
    resp_del = client.post(f"/income/delete/{inc_id}", follow_redirects=True)
    assert resp_del.status_code == 200

    with app.app_context():
        assert db.session.get(Income, inc_id) is None


def test_expense_crud(client, user_a, auth, app):
    auth.login("alice@example.com", "password123")

    with app.app_context():
        cat = ExpenseCategory.query.filter_by(name="Food", is_default=True).first()
        cat_id = cat.id

    # 1. Add expense
    resp = client.post(
        "/expenses/add",
        data={
            "amount": "85.50",
            "category_id": cat_id,
            "date": "2026-09-05",
            "description": "Weekly grocery shopping",
            "payment_method": "Debit Card"
        },
        follow_redirects=True
    )
    assert resp.status_code == 200
    assert b"recorded in Food" in resp.data

    with app.app_context():
        exp = Expense.query.filter_by(user_id=user_a).first()
        assert exp is not None
        assert exp.amount == 85.50
        exp_id = exp.id

    # 2. Edit expense
    resp_edit = client.post(
        f"/expenses/edit/{exp_id}",
        data={
            "amount": "92.00",
            "category_id": cat_id,
            "date": "2026-09-05",
            "description": "Updated grocery total",
            "payment_method": "Credit Card"
        },
        follow_redirects=True
    )
    assert resp_edit.status_code == 200

    with app.app_context():
        exp_updated = db.session.get(Expense, exp_id)
        assert exp_updated.amount == 92.00
        assert exp_updated.payment_method == "Credit Card"

    # 3. Delete expense
    client.post(f"/expenses/delete/{exp_id}", follow_redirects=True)
    with app.app_context():
        assert db.session.get(Expense, exp_id) is None


def test_savings_and_goal_crud(client, user_a, auth, app):
    auth.login("alice@example.com", "password123")

    # Add savings
    client.post(
        "/savings/add",
        data={
            "amount": "500.00",
            "source": "Emergency Fund",
            "date": "2026-09-10",
            "description": "Monthly safety deposit"
        },
        follow_redirects=True
    )
    with app.app_context():
        sav = Savings.query.filter_by(user_id=user_a).first()
        assert sav is not None
        assert sav.amount == 500.00

    # Add Financial Goal
    target_dt = (date.today() + timedelta(days=90)).strftime("%Y-%m-%d")
    client.post(
        "/goals/add",
        data={
            "name": "New Laptop",
            "target_amount": "1200.00",
            "current_amount": "400.00",
            "target_date": target_dt
        },
        follow_redirects=True
    )
    with app.app_context():
        goal = FinancialGoal.query.filter_by(user_id=user_a).first()
        assert goal is not None
        assert goal.remaining_amount == 800.00
        assert goal.percentage_complete == 33.3
        assert goal.required_monthly_saving > 0
        goal_id = goal.id

    # Contribute to Goal
    client.post(
        f"/goals/contribute/{goal_id}",
        data={"amount": "200.00"},
        follow_redirects=True
    )
    with app.app_context():
        g = db.session.get(FinancialGoal, goal_id)
        assert g.current_amount == 600.00
        assert g.percentage_complete == 50.0
