import json
from datetime import date
from app.extensions import db
from app.models.financial import ExpenseCategory


def test_api_income_endpoints(client, user_a, auth, app):
    auth.login("alice@example.com", "password123")

    # 1. POST /api/income
    post_resp = client.post(
        "/api/income",
        json={
            "amount": 3500.0,
            "source": "Freelance",
            "date": "2026-09-01",
            "description": "API Test Project"
        }
    )
    assert post_resp.status_code == 201
    data = post_resp.get_json()
    assert data["status"] == "success"
    income_id = data["data"]["id"]

    # 2. GET /api/income
    get_resp = client.get("/api/income")
    assert get_resp.status_code == 200
    get_data = get_resp.get_json()
    assert get_data["count"] >= 1

    # 3. PUT /api/income/<id>
    put_resp = client.put(
        f"/api/income/{income_id}",
        json={"amount": 3800.0, "description": "Updated via API"}
    )
    assert put_resp.status_code == 200
    assert put_resp.get_json()["data"]["amount"] == 3800.0

    # 4. DELETE /api/income/<id>
    del_resp = client.delete(f"/api/income/{income_id}")
    assert del_resp.status_code == 200


def test_api_expenses_and_dashboard(client, user_a, auth, app):
    auth.login("alice@example.com", "password123")

    with app.app_context():
        food_cat = ExpenseCategory.query.filter_by(name="Food", is_default=True).first()
        cat_id = food_cat.id

    # 1. POST /api/expenses
    post_resp = client.post(
        "/api/expenses",
        json={
            "amount": 75.0,
            "category_id": cat_id,
            "date": "2026-09-12",
            "description": "Lunch meeting",
            "payment_method": "Debit Card"
        }
    )
    assert post_resp.status_code == 201
    exp_id = post_resp.get_json()["data"]["id"]

    # 2. GET /api/dashboard
    dash_resp = client.get("/api/dashboard?year=2026&month=9")
    assert dash_resp.status_code == 200
    dash_data = dash_resp.get_json()
    assert dash_data["status"] == "success"
    assert "summary" in dash_data
    assert "health" in dash_data

    # 3. POST /api/ai/chat
    chat_resp = client.post(
        "/api/ai/chat",
        json={"message": "How can I reduce expenses?"}
    )
    assert chat_resp.status_code == 200
    assert "reply" in chat_resp.get_json()
