from datetime import date, timedelta
from app.extensions import db
from app.models.user import User
from app.models.financial import (
    Income,
    Expense,
    ExpenseCategory,
    Budget,
    Savings,
    FinancialGoal,
    FinancialAlert,
    AIRecommendation
)
from app.utils.helpers import seed_default_categories


class DemoService:
    @staticmethod
    def setup_demo_user(scenario: str = "salaried") -> User:
        """Creates or resets the demo user with rich data tailored to a chosen scenario."""
        seed_default_categories(db.session)

        demo_email = "demo@example.com"
        user = User.query.filter_by(email=demo_email).first()
        if not user:
            user = User(
                full_name="Demo User",
                email=demo_email,
                preferred_currency="USD"
            )
            user.set_password("password123")
            db.session.add(user)
            db.session.commit()

        # Clean existing demo data for this user
        Income.query.filter_by(user_id=user.id).delete()
        Expense.query.filter_by(user_id=user.id).delete()
        Budget.query.filter_by(user_id=user.id).delete()
        Savings.query.filter_by(user_id=user.id).delete()
        FinancialGoal.query.filter_by(user_id=user.id).delete()
        FinancialAlert.query.filter_by(user_id=user.id).delete()
        AIRecommendation.query.filter_by(user_id=user.id).delete()
        db.session.commit()

        # Fetch category map
        cats = {c.name: c.id for c in ExpenseCategory.query.filter_by(is_default=True).all()}

        today = date.today()
        current_year = today.year
        current_month = today.month

        if scenario == "student":
            # SCENARIO 2 — COLLEGE STUDENT
            user.full_name = "Alex Rivera (Student)"
            user.monthly_income = 1200.0
            user.monthly_savings_target = 150.0
            user.emergency_fund_target = 1000.0
            user.financial_goals_summary = "Save for textbooks, new laptop, and semester graduation trip."

            # Income
            db.session.add(Income(user_id=user.id, amount=800.0, source="Allowance", date=date(current_year, current_month, 1), description="Parental monthly allowance"))
            db.session.add(Income(user_id=user.id, amount=400.0, source="Scholarship", date=date(current_year, current_month, 5), description="Academic merit stipend"))

            # Budgets
            db.session.add(Budget(user_id=user.id, category_id=None, amount=1050.0, month=current_month, year=current_year))
            if "Food" in cats: db.session.add(Budget(user_id=user.id, category_id=cats["Food"], amount=350.0, month=current_month, year=current_year))
            if "Education" in cats: db.session.add(Budget(user_id=user.id, category_id=cats["Education"], amount=200.0, month=current_month, year=current_year))
            if "Transportation" in cats: db.session.add(Budget(user_id=user.id, category_id=cats["Transportation"], amount=100.0, month=current_month, year=current_year))
            if "Entertainment" in cats: db.session.add(Budget(user_id=user.id, category_id=cats["Entertainment"], amount=120.0, month=current_month, year=current_year))
            if "Shopping" in cats: db.session.add(Budget(user_id=user.id, category_id=cats["Shopping"], amount=100.0, month=current_month, year=current_year))

            # Expenses
            if "Food" in cats:
                db.session.add(Expense(user_id=user.id, category_id=cats["Food"], amount=42.50, date=date(current_year, current_month, 2), description="Campus cafeteria meals", payment_method="Debit Card"))
                db.session.add(Expense(user_id=user.id, category_id=cats["Food"], amount=110.00, date=date(current_year, current_month, 8), description="Weekly groceries at Trader Joe's", payment_method="Debit Card"))
                db.session.add(Expense(user_id=user.id, category_id=cats["Food"], amount=65.00, date=date(current_year, current_month, 14), description="Pizza night with roommates", payment_method="UPI"))
            if "Education" in cats:
                db.session.add(Expense(user_id=user.id, category_id=cats["Education"], amount=145.00, date=date(current_year, current_month, 3), description="Computer Science textbook", payment_method="Credit Card"))
            if "Transportation" in cats:
                db.session.add(Expense(user_id=user.id, category_id=cats["Transportation"], amount=50.00, date=date(current_year, current_month, 1), description="Monthly campus transit pass", payment_method="Debit Card"))
            if "Entertainment" in cats:
                db.session.add(Expense(user_id=user.id, category_id=cats["Entertainment"], amount=135.00, date=date(current_year, current_month, 12), description="Concert tickets & snacks (exceeded!)", payment_method="Credit Card"))
            if "Subscriptions" in cats:
                db.session.add(Expense(user_id=user.id, category_id=cats["Subscriptions"], amount=5.99, date=date(current_year, current_month, 4), description="Spotify Student", payment_method="Debit Card"))

            # Savings & Goals
            db.session.add(Savings(user_id=user.id, amount=120.0, date=date(current_year, current_month, 10), source="Savings Deposit", description="Saved from tutor gig"))
            db.session.add(Savings(user_id=user.id, amount=350.0, date=date(current_year, current_month - 1 if current_month > 1 else 12, 15), source="Savings Deposit", description="Prior savings"))
            db.session.add(FinancialGoal(user_id=user.id, name="Laptop Upgrade", target_amount=900.0, current_amount=470.0, target_date=today + timedelta(days=120), status="In Progress"))
            db.session.add(FinancialGoal(user_id=user.id, name="Emergency Buffer", target_amount=1000.0, current_amount=470.0, target_date=today + timedelta(days=180), status="In Progress"))

        elif scenario == "freelancer":
            # SCENARIO 3 — FREELANCER
            user.full_name = "Jordan Vance (Freelance Designer)"
            user.monthly_income = 6200.0
            user.monthly_savings_target = 1800.0
            user.emergency_fund_target = 15000.0
            user.financial_goals_summary = "Build a 6-month buffer for variable income months and invest in workstation setup."

            # Income (Multiple variable sources)
            db.session.add(Income(user_id=user.id, amount=2800.0, source="Freelance", date=date(current_year, current_month, 4), description="UI/UX design milestone - FinTech Client A"))
            db.session.add(Income(user_id=user.id, amount=2200.0, source="Freelance", date=date(current_year, current_month, 15), description="Web development sprint - Agency B"))
            db.session.add(Income(user_id=user.id, amount=1200.0, source="Business", date=date(current_year, current_month, 20), description="Design System kit sales"))

            # Budgets
            db.session.add(Budget(user_id=user.id, category_id=None, amount=3800.0, month=current_month, year=current_year))
            if "Rent" in cats: db.session.add(Budget(user_id=user.id, category_id=cats["Rent"], amount=1400.0, month=current_month, year=current_year))
            if "Food" in cats: db.session.add(Budget(user_id=user.id, category_id=cats["Food"], amount=600.0, month=current_month, year=current_year))
            if "Subscriptions" in cats: db.session.add(Budget(user_id=user.id, category_id=cats["Subscriptions"], amount=250.0, month=current_month, year=current_year))
            if "Bills" in cats: db.session.add(Budget(user_id=user.id, category_id=cats["Bills"], amount=200.0, month=current_month, year=current_year))
            if "Travel" in cats: db.session.add(Budget(user_id=user.id, category_id=cats["Travel"], amount=400.0, month=current_month, year=current_year))

            # Expenses
            if "Rent" in cats: db.session.add(Expense(user_id=user.id, category_id=cats["Rent"], amount=1400.00, date=date(current_year, current_month, 1), description="Home studio rent", payment_method="Bank Transfer"))
            if "Subscriptions" in cats:
                db.session.add(Expense(user_id=user.id, category_id=cats["Subscriptions"], amount=54.99, date=date(current_year, current_month, 2), description="Adobe Creative Cloud", payment_method="Credit Card"))
                db.session.add(Expense(user_id=user.id, category_id=cats["Subscriptions"], amount=32.00, date=date(current_year, current_month, 3), description="Figma Organization Plan", payment_method="Credit Card"))
                db.session.add(Expense(user_id=user.id, category_id=cats["Subscriptions"], amount=20.00, date=date(current_year, current_month, 5), description="GitHub Copilot & AI tools", payment_method="Credit Card"))
            if "Food" in cats:
                db.session.add(Expense(user_id=user.id, category_id=cats["Food"], amount=310.00, date=date(current_year, current_month, 10), description="Groceries & artisan coffee beans", payment_method="Debit Card"))
                db.session.add(Expense(user_id=user.id, category_id=cats["Food"], amount=180.00, date=date(current_year, current_month, 18), description="Client working lunches", payment_method="Credit Card"))
            if "Bills" in cats:
                db.session.add(Expense(user_id=user.id, category_id=cats["Bills"], amount=110.00, date=date(current_year, current_month, 7), description="High-speed fiber internet", payment_method="Bank Transfer"))

            # Savings & Goals
            db.session.add(Savings(user_id=user.id, amount=1500.0, date=date(current_year, current_month, 16), source="Emergency Fund", description="Freelance tax & rainy day cushion"))
            db.session.add(Savings(user_id=user.id, amount=7500.0, date=date(current_year, current_month - 1 if current_month > 1 else 12, 1), source="High-Yield Savings", description="Past quarterly reserves"))
            db.session.add(FinancialGoal(user_id=user.id, name="6-Month Income Buffer", target_amount=15000.0, current_amount=9000.0, target_date=today + timedelta(days=240), status="In Progress"))
            db.session.add(FinancialGoal(user_id=user.id, name="Pro Studio Display", target_amount=1600.0, current_amount=1100.0, target_date=today + timedelta(days=60), status="In Progress"))

        elif scenario == "household":
            # SCENARIO 4 — HOUSEHOLD MANAGER
            user.full_name = "Sarah & Marcus Sterling (Household)"
            user.monthly_income = 8500.0
            user.monthly_savings_target = 2200.0
            user.emergency_fund_target = 25000.0
            user.financial_goals_summary = "Manage multi-generational household expenses, college funds, and mortgage payoff."

            # Income
            db.session.add(Income(user_id=user.id, amount=5200.0, source="Salary", date=date(current_year, current_month, 1), description="Primary Partner Salary"))
            db.session.add(Income(user_id=user.id, amount=3300.0, source="Salary", date=date(current_year, current_month, 1), description="Secondary Partner Salary"))

            # Budgets
            db.session.add(Budget(user_id=user.id, category_id=None, amount=5800.0, month=current_month, year=current_year))
            if "Housing" in cats: db.session.add(Budget(user_id=user.id, category_id=cats["Housing"], amount=2100.0, month=current_month, year=current_year))
            if "Groceries" in cats: db.session.add(Budget(user_id=user.id, category_id=cats["Groceries"], amount=1100.0, month=current_month, year=current_year))
            if "Utilities" in cats: db.session.add(Budget(user_id=user.id, category_id=cats["Utilities"], amount=400.0, month=current_month, year=current_year))
            if "Education" in cats: db.session.add(Budget(user_id=user.id, category_id=cats["Education"], amount=700.0, month=current_month, year=current_year))
            if "Healthcare" in cats: db.session.add(Budget(user_id=user.id, category_id=cats["Healthcare"], amount=350.0, month=current_month, year=current_year))
            if "Transportation" in cats: db.session.add(Budget(user_id=user.id, category_id=cats["Transportation"], amount=450.0, month=current_month, year=current_year))

            # Expenses
            if "Housing" in cats: db.session.add(Expense(user_id=user.id, category_id=cats["Housing"], amount=2100.00, date=date(current_year, current_month, 1), description="Monthly mortgage payment", payment_method="Bank Transfer"))
            if "Groceries" in cats:
                db.session.add(Expense(user_id=user.id, category_id=cats["Groceries"], amount=385.00, date=date(current_year, current_month, 4), description="Costco bulk family run", payment_method="Credit Card"))
                db.session.add(Expense(user_id=user.id, category_id=cats["Groceries"], amount=245.00, date=date(current_year, current_month, 11), description="Weekly fresh market produce", payment_method="Credit Card"))
                db.session.add(Expense(user_id=user.id, category_id=cats["Groceries"], amount=290.00, date=date(current_year, current_month, 18), description="Mid-month supermarket restocking", payment_method="Credit Card"))
            if "Utilities" in cats:
                db.session.add(Expense(user_id=user.id, category_id=cats["Utilities"], amount=260.00, date=date(current_year, current_month, 6), description="Electric & Gas heating", payment_method="Bank Transfer"))
                db.session.add(Expense(user_id=user.id, category_id=cats["Utilities"], amount=85.00, date=date(current_year, current_month, 8), description="City water & trash", payment_method="Bank Transfer"))
            if "Healthcare" in cats:
                db.session.add(Expense(user_id=user.id, category_id=cats["Healthcare"], amount=220.00, date=date(current_year, current_month, 12), description="Pediatrician checkup & prescriptions", payment_method="Debit Card"))
            if "Education" in cats:
                db.session.add(Expense(user_id=user.id, category_id=cats["Education"], amount=450.00, date=date(current_year, current_month, 5), description="Children music & gymnastics classes", payment_method="Credit Card"))

            # Savings & Goals
            db.session.add(Savings(user_id=user.id, amount=2200.0, date=date(current_year, current_month, 15), source="Investment", description="Index fund contributions"))
            db.session.add(Savings(user_id=user.id, amount=18000.0, date=date(current_year, current_month - 1 if current_month > 1 else 12, 1), source="Emergency Fund", description="Household emergency reserve"))
            db.session.add(FinancialGoal(user_id=user.id, name="Family Emergency Fund", target_amount=25000.0, current_amount=20200.0, target_date=today + timedelta(days=200), status="In Progress"))
            db.session.add(FinancialGoal(user_id=user.id, name="College 529 Fund", target_amount=40000.0, current_amount=16500.0, target_date=today + timedelta(days=900), status="In Progress"))

        else:
            # SCENARIO 1 — SALARIED PROFESSIONAL (Default)
            user.full_name = "Elena Rostova (Salaried Engineer)"
            user.monthly_income = 5500.0
            user.monthly_savings_target = 1400.0
            user.emergency_fund_target = 18000.0
            user.financial_goals_summary = "Build 6-month safety net, save for vacation to Japan, and invest in index funds."

            # Income
            db.session.add(Income(user_id=user.id, amount=5500.0, source="Salary", date=date(current_year, current_month, 1), description="Monthly Tech Corp Net Salary"))

            # Budgets
            db.session.add(Budget(user_id=user.id, category_id=None, amount=3500.0, month=current_month, year=current_year))
            if "Rent" in cats: db.session.add(Budget(user_id=user.id, category_id=cats["Rent"], amount=1600.0, month=current_month, year=current_year))
            if "Food" in cats: db.session.add(Budget(user_id=user.id, category_id=cats["Food"], amount=600.0, month=current_month, year=current_year))
            if "Transportation" in cats: db.session.add(Budget(user_id=user.id, category_id=cats["Transportation"], amount=250.0, month=current_month, year=current_year))
            if "Entertainment" in cats: db.session.add(Budget(user_id=user.id, category_id=cats["Entertainment"], amount=300.0, month=current_month, year=current_year))
            if "Shopping" in cats: db.session.add(Budget(user_id=user.id, category_id=cats["Shopping"], amount=300.0, month=current_month, year=current_year))
            if "Utilities" in cats: db.session.add(Budget(user_id=user.id, category_id=cats["Utilities"], amount=200.0, month=current_month, year=current_year))

            # Expenses
            if "Rent" in cats: db.session.add(Expense(user_id=user.id, category_id=cats["Rent"], amount=1600.00, date=date(current_year, current_month, 1), description="Downtown Apartment Rent", payment_method="Bank Transfer"))
            if "Food" in cats:
                db.session.add(Expense(user_id=user.id, category_id=cats["Food"], amount=142.30, date=date(current_year, current_month, 3), description="Whole Foods groceries", payment_method="Credit Card"))
                db.session.add(Expense(user_id=user.id, category_id=cats["Food"], amount=78.50, date=date(current_year, current_month, 7), description="Dinner with colleagues", payment_method="Credit Card"))
                db.session.add(Expense(user_id=user.id, category_id=cats["Food"], amount=185.00, date=date(current_year, current_month, 14), description="Weekly grocery haul", payment_method="Debit Card"))
                db.session.add(Expense(user_id=user.id, category_id=cats["Food"], amount=94.00, date=date(current_year, current_month, 20), description="Weekend brunch & coffee", payment_method="Credit Card"))
            if "Transportation" in cats:
                db.session.add(Expense(user_id=user.id, category_id=cats["Transportation"], amount=65.00, date=date(current_year, current_month, 4), description="Gas refill", payment_method="Debit Card"))
                db.session.add(Expense(user_id=user.id, category_id=cats["Transportation"], amount=45.00, date=date(current_year, current_month, 16), description="Uber rides across city", payment_method="Credit Card"))
            if "Entertainment" in cats:
                db.session.add(Expense(user_id=user.id, category_id=cats["Entertainment"], amount=365.00, date=date(current_year, current_month, 10), description="Concert tickets + VIP lounge (Over budget!)", payment_method="Credit Card"))
            if "Shopping" in cats:
                db.session.add(Expense(user_id=user.id, category_id=cats["Shopping"], amount=210.00, date=date(current_year, current_month, 12), description="Spring wardrobe clothing", payment_method="Credit Card"))
            if "Utilities" in cats:
                db.session.add(Expense(user_id=user.id, category_id=cats["Utilities"], amount=145.00, date=date(current_year, current_month, 8), description="Electric & high speed internet", payment_method="Bank Transfer"))

            # Savings & Goals
            db.session.add(Savings(user_id=user.id, amount=1400.0, date=date(current_year, current_month, 2), source="High-Yield Savings", description="Automated 1st of month savings transfer"))
            db.session.add(Savings(user_id=user.id, amount=11000.0, date=date(current_year, current_month - 1 if current_month > 1 else 12, 1), source="Emergency Fund", description="Cumulative emergency savings"))
            db.session.add(FinancialGoal(user_id=user.id, name="Tokyo Vacation", target_amount=3500.0, current_amount=2100.0, target_date=today + timedelta(days=150), status="In Progress"))
            db.session.add(FinancialGoal(user_id=user.id, name="Emergency Fund (6-mo)", target_amount=18000.0, current_amount=12400.0, target_date=today + timedelta(days=220), status="In Progress"))

        # Pre-seed realistic AI recommendations
        db.session.add(AIRecommendation(
            user_id=user.id,
            recommendation_type="Budget",
            content=f"Based on your actual cashflow, you are maintaining a healthy balance overall. However, Entertainment spending is currently exceeding your planned threshold. Reallocating $75 from discretionary subscriptions could bring this back within bounds.",
            key_metrics="Entertainment > budget"
        ))
        db.session.add(AIRecommendation(
            user_id=user.id,
            recommendation_type="Savings",
            content=f"Your current monthly savings pace puts you on track to achieve your primary financial goal 2 months earlier than targeted! Keep automatic deposits enabled immediately on payday.",
            key_metrics="Savings pace positive"
        ))

        # Pre-seed alert
        db.session.add(FinancialAlert(
            user_id=user.id,
            type="Budget Exceeded",
            message="Entertainment spending has exceeded your monthly allocation. Consider pausing discretionary purchases until next month.",
            severity="danger",
            is_read=False
        ))

        db.session.commit()
        return user
