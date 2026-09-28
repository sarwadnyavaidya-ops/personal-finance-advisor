from app.extensions import db
from app.models.user import User


def test_register_success(client, app):
    """Test standard user registration."""
    resp = client.post(
        "/register",
        data={
            "full_name": "Charlie Test",
            "email": "charlie@example.com",
            "password": "mypassword",
            "confirm_password": "mypassword",
            "preferred_currency": "INR",
            "monthly_income": "60000"
        },
        follow_redirects=True
    )
    assert resp.status_code == 200
    assert b"Welcome to Personal Finance Advisor Bot" in resp.data

    with app.app_context():
        user = User.query.filter_by(email="charlie@example.com").first()
        assert user is not None
        assert user.full_name == "Charlie Test"
        assert user.preferred_currency == "INR"
        assert user.monthly_income == 60000.0
        # Check password hash is not stored in plaintext
        assert user.password_hash != "mypassword"
        assert user.check_password("mypassword") is True


def test_register_password_mismatch(client):
    """Test registration failure when passwords mismatch."""
    resp = client.post(
        "/register",
        data={
            "full_name": "Mismatch User",
            "email": "mismatch@example.com",
            "password": "password1",
            "confirm_password": "password2"
        },
        follow_redirects=True
    )
    assert b"Passwords do not match" in resp.data


def test_login_and_logout(client, user_a, auth):
    """Test successful login and subsequent logout."""
    resp = auth.login("alice@example.com", "password123")
    assert resp.status_code == 200
    assert b"Welcome back, Alice User" in resp.data

    # Log out
    resp_out = auth.logout()
    assert resp_out.status_code == 200
    assert b"logged out" in resp_out.data


def test_login_invalid_credentials(client, user_a, auth):
    """Test login with wrong password."""
    resp = auth.login("alice@example.com", "wrongpassword")
    assert b"Invalid email or password" in resp.data


def test_update_profile(client, user_a, auth, app):
    """Test updating user profile financial targets."""
    auth.login("alice@example.com", "password123")
    resp = client.post(
        "/profile",
        data={
            "action": "update_profile",
            "full_name": "Alice Updated",
            "preferred_currency": "GBP",
            "monthly_income": "6500",
            "monthly_savings_target": "1500",
            "emergency_fund_target": "20000",
            "financial_goals_summary": "Updated financial plan notes."
        },
        follow_redirects=True
    )
    assert resp.status_code == 200
    assert b"Profile updated successfully" in resp.data

    with app.app_context():
        user = db.session.get(User, user_a)
        assert user.full_name == "Alice Updated"
        assert user.preferred_currency == "GBP"
        assert user.currency_symbol == "£"
        assert user.monthly_income == 6500.0
        assert user.monthly_savings_target == 1500.0
        assert user.emergency_fund_target == 20000.0
