from datetime import date
from app.extensions import db
from app.models.financial import Income, Expense, ExpenseCategory


def test_user_data_isolation(client, user_a, user_b, auth, app):
    """Ensure strict isolation: User B cannot access, view, or mutate User A's records."""
    today = date.today()

    with app.app_context():
        food_cat = ExpenseCategory.query.filter_by(name="Food", is_default=True).first()

        # Create record belonging exclusively to User A
        income_a = Income(
            user_id=user_a,
            amount=9999.0,
            source="Salary",
            date=today,
            description="Alice Private Income"
        )
        expense_a = Expense(
            user_id=user_a,
            category_id=food_cat.id,
            amount=777.0,
            date=today,
            description="Alice Private Expense"
        )
        db.session.add_all([income_a, expense_a])
        db.session.commit()
        inc_a_id = income_a.id
        exp_a_id = expense_a.id

    # Now login as User B (Bob)
    auth.login("bob@example.com", "secret456")

    # 1. User B accesses income page: User A's income MUST NOT appear
    resp_inc = client.get("/income")
    assert resp_inc.status_code == 200
    assert b"Alice Private Income" not in resp_inc.data
    assert b"9999.00" not in resp_inc.data

    # 2. User B tries to view or edit User A's income directly
    resp_edit = client.get(f"/income/edit/{inc_a_id}")
    assert resp_edit.status_code == 404

    # 3. User B tries to delete User A's income directly
    resp_del_inc = client.post(f"/income/delete/{inc_a_id}")
    assert resp_del_inc.status_code == 404

    # 4. User B tries to delete User A's expense directly
    resp_del_exp = client.post(f"/expenses/delete/{exp_a_id}")
    assert resp_del_exp.status_code == 404

    # 5. User B tries to fetch User A's income via REST API
    resp_api = client.get(f"/api/income/{inc_a_id}")
    assert resp_api.status_code == 404

    # Verify User A's records are intact and unaffected in the database
    with app.app_context():
        assert db.session.get(Income, inc_a_id) is not None
        assert db.session.get(Expense, exp_a_id) is not None
