import sys
from app import create_app
from app.services.demo_service import DemoService

app = create_app("development")

if __name__ == "__main__":
    scenario = sys.argv[1] if len(sys.argv) > 1 else "salaried"
    valid = ["salaried", "student", "freelancer", "household"]
    if scenario not in valid:
        print(f"Unknown scenario '{scenario}'. Choose from: {', '.join(valid)}")
        sys.exit(1)

    with app.app_context():
        user = DemoService.setup_demo_user(scenario)
        print("=" * 60)
        print(f"SUCCESS: Seeded demo data for scenario: '{scenario.upper()}'")
        print(f"Login Email:    {user.email}")
        print(f"Login Password: password123")
        print(f"Full Name:      {user.full_name}")
        print(f"Monthly Income: {user.currency_symbol}{user.monthly_income:,.2f}")
        print("=" * 60)
