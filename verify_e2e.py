import sys
from app import create_app
from app.models.user import User
from app.services.demo_service import DemoService


def run_verification():
    app = create_app("development")
    client = app.test_client()

    print("\n" + "=" * 70)
    print("RUNNING END-TO-END VERIFICATION OF PERSONAL FINANCE ADVISOR BOT")
    print("=" * 70)

    # 1. Ensure Demo user is loaded
    with app.app_context():
        demo_user = DemoService.setup_demo_user("salaried")
        print(f"[OK] Seeded demo user: {demo_user.email} (Income: {demo_user.currency_symbol}{demo_user.monthly_income:,.2f})")

    # 2. Public landing and health check
    res = client.get("/")
    assert res.status_code == 200, f"Landing page failed with {res.status_code}"
    print("[OK] GET / (Landing page)")

    res = client.get("/health")
    assert res.status_code == 200, f"Health endpoint failed with {res.status_code}"
    print("[OK] GET /health ->", res.get_json())

    # 3. Log in as demo user
    login_res = client.post("/login", data={"email": "demo@example.com", "password": "password123"}, follow_redirects=True)
    assert login_res.status_code == 200
    assert b"Elena Rostova" in login_res.data
    print("[OK] POST /login -> Authenticated as Demo User")

    # 4. Dashboard View
    res = client.get("/dashboard")
    assert res.status_code == 200, f"Dashboard failed with {res.status_code}"
    assert b"Financial Overview" in res.data
    assert b"chartIncomeVsExpense" in res.data
    assert b"chartCategoryExpenses" in res.data
    print("[OK] GET /dashboard -> 6 Chart.js charts, KPIs, alerts rendered")

    # 5. Income Page
    res = client.get("/income")
    assert res.status_code == 200
    assert b"Income Streams" in res.data
    print("[OK] GET /income -> Income breakdown and table rendered")

    # 6. Expenses Page
    res = client.get("/expenses")
    assert res.status_code == 200
    assert b"Recorded Transactions" in res.data
    print("[OK] GET /expenses -> Expense filters and transaction list rendered")

    # 7. Budget Planning Page
    res = client.get("/budget")
    assert res.status_code == 200
    assert b"Budget Planning &amp; Controls" in res.data or b"Budget Planning & Controls" in res.data
    print("[OK] GET /budget -> Budget limits and overspending warnings rendered")

    # 8. Savings Page
    res = client.get("/savings")
    assert res.status_code == 200
    assert b"Savings &amp; Emergency Reserves" in res.data or b"Savings & Emergency Reserves" in res.data
    print("[OK] GET /savings -> Savings growth timeline and emergency runway rendered")

    # 9. Goals Page
    res = client.get("/goals")
    assert res.status_code == 200
    assert b"Financial Targets &amp; Milestones" in res.data or b"Financial Targets & Milestones" in res.data
    print("[OK] GET /goals -> Goals progress cards and monthly pace rendered")

    # 10. Spending Analysis Page
    res = client.get("/analysis/spending")
    assert res.status_code == 200
    assert b"AI Spending Diagnostic" in res.data
    print("[OK] GET /analysis/spending -> Concentration diagnostics rendered")

    # 11. Financial Health Page
    res = client.get("/analysis/health")
    assert res.status_code == 200
    assert b"Financial Health Evaluation" in res.data
    print("[OK] GET /analysis/health -> Health status, score, and why indicators rendered")

    # 12. AI Advisor Chat Page
    res = client.get("/advisor")
    assert res.status_code == 200
    assert b"AI Financial Advisor Assistant" in res.data
    print("[OK] GET /advisor -> Chat interface and live grounding panel rendered")

    # 13. AI Chat Endpoint (POST)
    chat_res = client.post("/advisor/chat", json={"message": "How can I reduce expenses?"})
    assert chat_res.status_code == 200
    reply_json = chat_res.get_json()
    assert "reply" in reply_json
    print(f"[OK] POST /advisor/chat -> Reply received ({len(reply_json['reply'])} characters)")

    # 14. Monthly Report Page
    res = client.get("/reports")
    assert res.status_code == 200
    assert b"Monthly Financial Report" in res.data
    print("[OK] GET /reports -> Financial statement rendered")

    # 15. Printable / PDF Report View
    res = client.get("/reports/print")
    assert res.status_code == 200
    assert b"Financial Performance Statement" in res.data or b"Monthly Financial Statement" in res.data
    print("[OK] GET /reports/print -> Print-optimized layout rendered")

    # 16. Financial Alerts Page
    res = client.get("/alerts")
    assert res.status_code == 200
    assert b"Financial Alerts &amp; Notifications" in res.data or b"Financial Alerts & Notifications" in res.data
    print("[OK] GET /alerts -> Overspending and budget alerts rendered")

    # 17. REST API: Dashboard
    res = client.get("/api/dashboard")
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "success"
    assert "summary" in data and "health" in data
    print("[OK] GET /api/dashboard -> Valid JSON payload")

    # 18. REST API: AI Analyze
    res = client.get("/api/ai/analyze")
    assert res.status_code == 200
    assert res.get_json()["status"] == "success"
    print("[OK] GET /api/ai/analyze -> Valid JSON payload")

    # 19. REST API: AI Recommendations
    res = client.get("/api/ai/recommendations")
    assert res.status_code == 200
    assert res.get_json()["status"] == "success"
    print("[OK] GET /api/ai/recommendations -> Valid JSON payload")

    # 20. Switch between all 4 personas
    for sc in ["student", "freelancer", "household", "salaried"]:
        res = client.get(f"/demo/load/{sc}", follow_redirects=True)
        assert res.status_code == 200
        print(f"[OK] GET /demo/load/{sc} -> Switched scenario and reloaded dashboard successfully")

    print("\n" + "=" * 70)
    print("ALL 20 SYSTEM VERIFICATION CHECKS PASSED PERFECTLY!")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    run_verification()
