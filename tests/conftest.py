import pytest
from app import create_app
from app.extensions import db
from app.models.user import User
from app.utils.helpers import seed_default_categories


@pytest.fixture
def app():
    """Create and configure a clean testing app instance."""
    app_instance = create_app("testing")
    with app_instance.app_context():
        db.create_all()
        seed_default_categories(db.session)
        yield app_instance
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()


@pytest.fixture
def user_a(app):
    """Create a primary test user."""
    with app.app_context():
        user = User(
            full_name="Alice User",
            email="alice@example.com",
            preferred_currency="USD",
            monthly_income=5000.0,
            monthly_savings_target=1000.0,
            emergency_fund_target=15000.0
        )
        user.set_password("password123")
        db.session.add(user)
        db.session.commit()
        return user.id


@pytest.fixture
def user_b(app):
    """Create a second test user to test cross-user isolation."""
    with app.app_context():
        user = User(
            full_name="Bob User",
            email="bob@example.com",
            preferred_currency="EUR",
            monthly_income=4000.0,
            monthly_savings_target=800.0,
            emergency_fund_target=12000.0
        )
        user.set_password("secret456")
        db.session.add(user)
        db.session.commit()
        return user.id


class AuthActions:
    def __init__(self, client):
        self._client = client

    def login(self, email="alice@example.com", password="password123"):
        return self._client.post(
            "/login",
            data={"email": email, "password": password},
            follow_redirects=True
        )

    def logout(self):
        return self._client.get("/logout", follow_redirects=True)


@pytest.fixture
def auth(client):
    return AuthActions(client)
